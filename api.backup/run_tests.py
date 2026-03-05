import urllib.request
import urllib.error
import json
import time

def test_endpoint(method, url, data=None, description=""):
    """Test an API endpoint and return results"""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"{'='*70}")
    print(f"{method} {url}")
    
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    if data:
        print(f"Payload: {json.dumps(data, indent=2)}")
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=headers, method=method)
    else:
        req = urllib.request.Request(url, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            status = response.getcode()
            body = response.read().decode('utf-8')
            print(f"\n[PASS] Status: {status}")
            
            if body:
                try:
                    parsed = json.loads(body)
                    if method == "GET" and "_id" in parsed:
                        print(f"ID: {parsed['_id']}")
                    return True, status, parsed
                except:
                    return True, status, body
            return True, status, None
                
    except urllib.error.HTTPError as e:
        print(f"\n[FAIL] HTTP {e.code}: {e.reason}")
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            print(f"Error: {error_data.get('detail', error_body)}")
            return False, e.code, error_data
        except:
            print(f"Error: {error_body}")
            return False, e.code, error_body
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        return False, None, str(e)

# Test Configuration
BASE_URL = "http://127.0.0.1:8015"
test_results = []

print("="*70)
print("COMPREHENSIVE API TEST SUITE")
print("="*70)

# ============================================================================
# 1. ASSETS API TESTS
# ============================================================================
print("\n\n" + "="*70)
print("SECTION 1: ASSETS API")
print("="*70)

# Test 1.1: GET Asset (verify schema fix)
success, status, data = test_endpoint(
    "GET",
    f"{BASE_URL}/assets/CAM_GATE3_001",
    description="1.1 - GET Asset (schema typo fix verification)"
)
test_results.append(("Assets GET", success))

# Test 1.2: PUT Asset - Partial update (FPS only)
success, status, data = test_endpoint(
    "PUT",
    f"{BASE_URL}/assets/CAM_GATE3_001",
    {
        "asset_info": {
            "camera": {
                "stream": {
                    "fps": 20
                }
            }
        }
    },
    description="1.2 - PUT Asset - Partial nested update (FPS only)"
)
test_results.append(("Assets PUT - Partial Update", success))

# Test 1.3: Verify partial update preserved other fields
if success and data:
    fps = data.get('asset_info', {}).get('camera', {}).get('stream', {}).get('fps')
    rtsp = data.get('asset_info', {}).get('camera', {}).get('stream', {}).get('rtsp_url')
    asset_type = data.get('asset_info', {}).get('type')
    
    print(f"\nVerification:")
    print(f"  FPS updated: {fps == 20}")
    print(f"  RTSP URL preserved: {rtsp is not None}")
    print(f"  Asset type preserved: {asset_type is not None}")
    
    if fps == 20 and rtsp and asset_type:
        print("[PASS] Partial update correctly merged!")
        test_results.append(("Assets PUT - Field Preservation", True))
    else:
        print("[FAIL] Some fields were lost!")
        test_results.append(("Assets PUT - Field Preservation", False))

# ============================================================================
# 2. MODELS API TESTS
# ============================================================================
print("\n\n" + "="*70)
print("SECTION 2: MODELS API")
print("="*70)

# Test 2.1: POST Model with unique ID
unique_id = f"MODEL_TEST_{int(time.time())}"
success, status, data = test_endpoint(
    "POST",
    f"{BASE_URL}/models",
    {
        "_id": unique_id,
        "tenant_id": "TENANT_01",
        "site_id": "SITE_02",
        "gateway_id": "GW_SITE_02_0001",
        "name": "Test Model",
        "framework_id": "tensorflow",
        "status": "ACTIVE"
    },
    description="2.1 - POST Model (Timestamps fix verification)"
)
test_results.append(("Models POST - New Model", success and status == 201))

# Test 2.2: Verify timestamps in response
if success and data:
    has_created = 'created_at' in data
    has_updated = 'updated_at' in data
    print(f"\nTimestamp Verification:")
    print(f"  Has created_at: {has_created}")
    print(f"  Has updated_at: {has_updated}")
    
    if has_created and has_updated:
        print("[PASS] Timestamps present in response!")
        test_results.append(("Models POST - Timestamps", True))
    else:
        print("[FAIL] Missing timestamps!")
        test_results.append(("Models POST - Timestamps", False))

# Test 2.3: POST duplicate model (should return 409)
success, status, data = test_endpoint(
    "POST",
    f"{BASE_URL}/models",
    {
        "_id": unique_id,
        "tenant_id": "TENANT_01",
        "site_id": "SITE_02",
        "gateway_id": "GW_SITE_02_0001",
        "name": "Duplicate Model",
        "framework_id": "pytorch",
        "status": "ACTIVE"
    },
    description="2.2 - POST Duplicate Model (should return 409)"
)
test_results.append(("Models POST - Duplicate Handling", not success and status == 409))

# ============================================================================
# 3. ACTIONS API TESTS
# ============================================================================
print("\n\n" + "="*70)
print("SECTION 3: ACTIONS API")
print("="*70)

# Test 3.1: POST Action with _id
unique_action_id = f"ACT_TEST_{int(time.time())}"
success, status, data = test_endpoint(
    "POST",
    f"{BASE_URL}/actions",
    {
        "_id": unique_action_id,
        "tenant_id": "TENANT_01",
        "site_id": "SITE_01",
        "gateway_id": "GW_SITE_01_0001",
        "event_id": "EVT_20260112_001",
        "policy_id": "POLICY_PPE_SITE_01_0001",
        "route_severity": "WARNING",
        "decisions": []
    },
    description="3.1 - POST Action (schema _id fix verification)"
)
test_results.append(("Actions POST - With _id", success and status == 201))

# Test 3.2: GET Action
if success:
    success, status, data = test_endpoint(
        "GET",
        f"{BASE_URL}/actions/{unique_action_id}",
        description="3.2 - GET Action"
    )
    test_results.append(("Actions GET", success))

# ============================================================================
# 4. GATEWAY API TESTS (Quick verification)
# ============================================================================
print("\n\n" + "="*70)
print("SECTION 4: GATEWAY API (Quick Check)")
print("="*70)

success, status, data = test_endpoint(
    "GET",
    f"{BASE_URL}/gateway?limit=1",
    description="4.1 - List Gateways"
)
test_results.append(("Gateway List", success))

# ============================================================================
# TEST SUMMARY
# ============================================================================
print("\n\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

passed = sum(1 for _, result in test_results if result)
failed = sum(1 for _, result in test_results if not result)
total = len(test_results)

print(f"\nTotal Tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Success Rate: {(passed/total*100):.1f}%")

print("\nDetailed Results:")
for test_name, result in test_results:
    status_icon = "[PASS]" if result else "[FAIL]"
    print(f"  {status_icon} {test_name}")

if failed == 0:
    print("\n" + "="*70)
    print("ALL TESTS PASSED!")
    print("="*70)
else:
    print("\n" + "="*70)
    print(f"SOME TESTS FAILED ({failed}/{total})")
    print("="*70)
