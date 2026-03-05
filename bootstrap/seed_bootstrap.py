#!/usr/bin/env python3
"""
seed_bootstrap.py
Single-file bootstrap seeder for MongoDB (database: hmi)

Supports seeding collections:
  - gateway
  - personnel
  - policies
  - assets
  - profiles 
  - models   

Features:
  - mode=upsert (default) or insert
  - optional drop
  - optional dry-run
  - timestamps handling (created_at/updated_at)
  - lenient JSON loader to tolerate trailing commas (--lenient-json)
  - referential sanity checks with warnings (strict optional: --strict-refs)
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


DEFAULT_DB = "hmi"
DEFAULT_URI = "mongodb://localhost:27017"


# -----------------------------
# Helpers
# -----------------------------
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: Any) -> Any:
    """
    Convert ISO-8601 string ending with Z -> aware datetime.
    Leave other values unchanged.
    """
    if isinstance(value, str):
        v = value.strip()
        if v.endswith("Z"):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                return value
    return value


def normalize_doc(doc: Dict[str, Any], add_timestamps: bool = True) -> Dict[str, Any]:
    """
    Convert known timestamp fields and optionally set created_at/updated_at.
    """
    for k in ["created_at", "updated_at", "last_seen_at", "detected_at", "sent_at"]:
        if k in doc:
            doc[k] = parse_dt(doc[k])

    # Nested: actions.decisions[*].sent_at (if ever used in future seeds)
    if isinstance(doc.get("decisions"), list):
        for d in doc["decisions"]:
            if isinstance(d, dict) and "sent_at" in d:
                d["sent_at"] = parse_dt(d["sent_at"])

    if add_timestamps:
        now = utc_now()
        doc.setdefault("created_at", now)
        doc["updated_at"] = now

    return doc


def strip_trailing_commas(s: str) -> str:
    """
    Minimal preprocessor to allow JSON-like inputs with trailing commas:
      - removes ",}" and ",]" patterns (ignores whitespace/newlines between)
    This is not a full JSON5 parser, but works for the seed you provided.
    """
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)
    return s


def load_seed_file(path: str, lenient_json: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    raw = ""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    if lenient_json:
        raw = strip_trailing_commas(raw)

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("Seed file must be a JSON object at the top-level.")

    # Accept both singular and plural keys for model/profile
    # and also allow missing keys (treated as empty lists).
    normalized: Dict[str, List[Dict[str, Any]]] = {}

    def as_list(key: str) -> List[Dict[str, Any]]:
        v = data.get(key, [])
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError(f"Seed key '{key}' must be a list")
        return v

    normalized["gateway"] = as_list("gateway")
    normalized["personnel"] = as_list("personnel")
    normalized["policies"] = as_list("policies")
    normalized["assets"] = as_list("assets")

    # profile(s)
    profiles = data.get("profiles", None)
    if profiles is None:
        profiles = data.get("profile", [])
    if profiles is None:
        profiles = []
    if not isinstance(profiles, list):
        raise ValueError("Seed key 'profiles' or 'profile' must be a list")
    normalized["profiles"] = profiles

    # model(s)
    models = data.get("models", None)
    if models is None:
        models = data.get("model", [])
    if models is None:
        models = []
    if not isinstance(models, list):
        raise ValueError("Seed key 'models' or 'model' must be a list")
    normalized["models"] = models

    return normalized


def required_keys_present(doc: Dict[str, Any], required: List[str]) -> Tuple[bool, str]:
    missing = [k for k in required if k not in doc or doc[k] in (None, "")]
    if missing:
        return False, f"Missing required keys: {missing}"
    return True, ""


def index_by_id(items: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for it in items:
        if isinstance(it, dict) and "_id" in it:
            out[str(it["_id"])] = it
    return out


def _safe_id(doc: Dict[str, Any]) -> str:
    return str(doc.get("_id", "<missing _id>"))


# -----------------------------
# Referential sanity checks
# -----------------------------
def validate_policy_person_targets(policies: List[Dict[str, Any]], personnel_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for p in policies:
        pid = p.get("_id", "<missing _id>")
        routes = p.get("routes", [])
        if not isinstance(routes, list):
            continue
        for r in routes:
            targets = r.get("targets", [])
            if not isinstance(targets, list):
                continue
            for t in targets:
                if not isinstance(t, dict):
                    continue
                if t.get("target_type") == "PERSON":
                    person_id = str(t.get("value", "")).strip()
                    if person_id and person_id not in personnel_by_id:
                        errors.append(
                            f"Policy '{pid}': PERSON target '{person_id}' not found in personnel seeds"
                        )
    return errors


def validate_assets_gateway_refs(assets: List[Dict[str, Any]], gateways_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for a in assets:
        aid = a.get("_id", "<missing _id>")
        gw = str(a.get("gateway_id", "")).strip()
        if gw and gw not in gateways_by_id:
            errors.append(f"Asset '{aid}': gateway_id '{gw}' not found in gateway seeds")
    return errors


def validate_assets_policy_refs(assets: List[Dict[str, Any]], policies_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Your assets contain asset_info.bindings.assigned_policy_id (in your new seed),
    while earlier schema had 'assined_policy_id'. We validate both.
    """
    errors: List[str] = []
    for a in assets:
        aid = a.get("_id", "<missing _id>")
        bindings = (((a.get("asset_info") or {}).get("bindings")) or {})
        if not isinstance(bindings, dict):
            continue
        pid = bindings.get("assigned_policy_id") or bindings.get("assined_policy_id") or ""
        pid = str(pid).strip()
        if pid and pid not in policies_by_id:
            errors.append(f"Asset '{aid}': bound policy '{pid}' not found in policy seeds")
    return errors


def validate_assets_model_refs(assets: List[Dict[str, Any]], models_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for a in assets:
        aid = a.get("_id", "<missing _id>")
        bindings = (((a.get("asset_info") or {}).get("bindings")) or {})
        if not isinstance(bindings, dict):
            continue
        mid = str(bindings.get("assigned_model_id", "")).strip()
        if mid and mid not in models_by_id:
            errors.append(f"Asset '{aid}': bound model '{mid}' not found in model seeds")
    return errors


def validate_assets_profile_refs(assets: List[Dict[str, Any]], profiles_by_id: Dict[str, Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    for a in assets:
        aid = a.get("_id", "<missing _id>")
        bindings = (((a.get("asset_info") or {}).get("bindings")) or {})
        if not isinstance(bindings, dict):
            continue
        pids = bindings.get("target_profile_ids", [])
        if pids is None:
            continue
        if not isinstance(pids, list):
            errors.append(f"Asset '{aid}': target_profile_ids must be a list")
            continue
        for pid in pids:
            pid_s = str(pid).strip()
            if pid_s and pid_s not in profiles_by_id:
                errors.append(f"Asset '{aid}': target_profile_id '{pid_s}' not found in profile seeds")
    return errors


# -----------------------------
# Seeding logic
# -----------------------------
def seed_collection(col, items: List[Dict[str, Any]], mode: str, add_timestamps: bool, dry_run: bool) -> Dict[str, int]:
    stats = {"processed": 0, "inserted": 0, "updated": 0, "skipped": 0, "errors": 0}

    for raw in items:
        stats["processed"] += 1

        if not isinstance(raw, dict):
            stats["errors"] += 1
            print(f"[ERROR] Item is not a JSON object: {raw}", file=sys.stderr)
            continue

        ok, msg = required_keys_present(raw, ["_id", "tenant_id", "site_id"])
        if not ok:
            stats["errors"] += 1
            print(f"[ERROR] {col.name}: {_safe_id(raw)} - {msg}", file=sys.stderr)
            continue

        doc = normalize_doc(dict(raw), add_timestamps=add_timestamps)
        _id = doc["_id"]

        if dry_run:
            existing = col.find_one({"_id": _id})
            if mode == "insert":
                if existing:
                    stats["skipped"] += 1
                else:
                    stats["inserted"] += 1
            else:  # upsert
                if existing:
                    # could be skip if identical; we approximate as "updated"
                    stats["updated"] += 1
                else:
                    stats["inserted"] += 1
            continue

        try:
            if mode == "insert":
                col.insert_one(doc)
                stats["inserted"] += 1
            elif mode == "upsert":
                patch = dict(doc)
                patch.pop("_id", None)
                res = col.update_one({"_id": _id}, {"$set": patch}, upsert=True)
                if res.upserted_id is not None:
                    stats["inserted"] += 1
                elif res.modified_count > 0:
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            else:
                stats["errors"] += 1
                print(f"[ERROR] Unknown mode: {mode}", file=sys.stderr)
        except DuplicateKeyError:
            stats["errors"] += 1
            print(f"[ERROR] Duplicate _id '{_id}' in {col.name} (mode=insert)", file=sys.stderr)
        except Exception as e:
            stats["errors"] += 1
            print(f"[ERROR] {col.name} _id='{_id}': {e}", file=sys.stderr)

    return stats


def ensure_indexes(db) -> None:
    """
    Basic, practical indexes for seeded collections.
    """
    db["gateway"].create_index([("tenant_id", 1), ("site_id", 1)])
    db["gateway"].create_index([("status", 1)])

    db["personnel"].create_index([("tenant_id", 1), ("site_id", 1)])
    db["personnel"].create_index([("role", 1), ("on_call", 1)])

    db["policies"].create_index([("tenant_id", 1), ("site_id", 1)])
    db["policies"].create_index([("anomaly_type", 1), ("enabled", 1)])
    db["policies"].create_index([("priority", -1)])

    db["assets"].create_index([("tenant_id", 1), ("site_id", 1), ("gateway_id", 1)])
    db["assets"].create_index([("status", 1)])
    db["assets"].create_index([("asset_info.type", 1)])
    db["assets"].create_index([("asset_info.tags", 1)])

    db["profiles"].create_index([("tenant_id", 1), ("site_id", 1)])
    db["profiles"].create_index([("targets", 1)])

    db["models"].create_index([("tenant_id", 1), ("site_id", 1), ("gateway_id", 1)])
    db["models"].create_index([("status", 1), ("framework_id", 1)])


def warn_or_fail(errors: List[str], strict: bool, title: str) -> None:
    if not errors:
        return
    if strict:
        print(f"[ERROR] {title}:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(2)
    else:
        print(f"[WARN] {title}:")
        for e in errors:
            print(f"  - {e}")


def main():
    parser = argparse.ArgumentParser(description="Seed bootstrap for HMI MongoDB")
    parser.add_argument("--uri", default=DEFAULT_URI, help=f"MongoDB URI (default: {DEFAULT_URI})")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"Database name (default: {DEFAULT_DB})")
    parser.add_argument("--seed", required=True, help="Path to seed JSON file")
    parser.add_argument("--lenient-json", action="store_true", help="Allow trailing commas in seed JSON")
    parser.add_argument(
        "--mode",
        choices=["insert", "upsert"],
        default="upsert",
        help="insert=fail on duplicates, upsert=idempotent create/update (default: upsert)",
    )
    parser.add_argument("--no-timestamps", action="store_true", help="Do not auto-add created_at/updated_at")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without writing to DB")
    parser.add_argument("--drop", action="store_true", help="Drop seeded collections before seeding")
    parser.add_argument(
        "--strict-refs",
        action="store_true",
        help="Fail if referential checks fail (otherwise warns and continues)",
    )
    args = parser.parse_args()

    seed = load_seed_file(args.seed, lenient_json=args.lenient_json)

    gateways = seed["gateway"]
    personnel = seed["personnel"]
    policies = seed["policies"]
    assets = seed["assets"]
    profiles = seed["profiles"]
    models = seed["models"]

    # Referential sanity checks
    gateways_by_id = index_by_id(gateways)
    personnel_by_id = index_by_id(personnel)
    policies_by_id = index_by_id(policies)
    profiles_by_id = index_by_id(profiles)
    models_by_id = index_by_id(models)

    warn_or_fail(
        validate_policy_person_targets(policies, personnel_by_id),
        args.strict_refs,
        "Policy PERSON targets refer to missing personnel in seed",
    )
    warn_or_fail(
        validate_assets_gateway_refs(assets, gateways_by_id),
        args.strict_refs,
        "Assets refer to missing gateways in seed",
    )
    warn_or_fail(
        validate_assets_policy_refs(assets, policies_by_id),
        args.strict_refs,
        "Assets refer to missing policies in seed (bindings.assigned_policy_id/assined_policy_id)",
    )
    warn_or_fail(
        validate_assets_model_refs(assets, models_by_id),
        args.strict_refs,
        "Assets refer to missing models in seed (bindings.assigned_model_id)",
    )
    warn_or_fail(
        validate_assets_profile_refs(assets, profiles_by_id),
        args.strict_refs,
        "Assets refer to missing profiles in seed (bindings.target_profile_ids)",
    )

    client = MongoClient(args.uri)
    db = client[args.db]
    ensure_indexes(db)

    if args.drop:
        cols = ["gateway", "personnel", "policies", "assets", "profiles", "models"]
        if not args.dry_run:
            for c in cols:
                db[c].drop()
            ensure_indexes(db)
        print(f"[INFO] Dropped collections: {', '.join(cols)}")

    add_ts = not args.no_timestamps
    print(f"[INFO] Seeding DB='{args.db}' mode='{args.mode}' dry_run={args.dry_run} timestamps={add_ts}")

    # Recommended seed order
    gw_stats = seed_collection(db["gateway"], gateways, args.mode, add_ts, args.dry_run)
    pe_stats = seed_collection(db["personnel"], personnel, args.mode, add_ts, args.dry_run)
    pr_stats = seed_collection(db["profiles"], profiles, args.mode, add_ts, args.dry_run)
    mo_stats = seed_collection(db["models"], models, args.mode, add_ts, args.dry_run)
    po_stats = seed_collection(db["policies"], policies, args.mode, add_ts, args.dry_run)
    as_stats = seed_collection(db["assets"], assets, args.mode, add_ts, args.dry_run)

    print("\n[RESULT] gateway:", gw_stats)
    print("[RESULT] personnel:", pe_stats)
    print("[RESULT] profiles:", pr_stats)
    print("[RESULT] models:", mo_stats)
    print("[RESULT] policies:", po_stats)
    print("[RESULT] assets:", as_stats)

    client.close()


if __name__ == "__main__":
    main()
