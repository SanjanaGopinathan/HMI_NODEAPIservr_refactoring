import { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';
import { useConfig } from './ConfigContext';
import { queries } from '../../lib/api';
import { useQuery } from '@tanstack/react-query';

function Switch({ checked, onChange }: { checked: boolean; onChange: () => void }) {
    return (
        <button
            type="button"
            role="switch"
            aria-checked={checked}
            onClick={onChange}
            className={`
                relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 focus:ring-offset-slate-900
                ${checked ? 'bg-indigo-600' : 'bg-slate-700'}
            `}
        >
            <span
                aria-hidden="true"
                className={`
                    pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out
                    ${checked ? 'translate-x-5' : 'translate-x-0'}
                `}
            />
        </button>
    );
}

export function SettingsPage() {
    const { tenant_id, site_id, gateway_id, updateConfig } = useConfig();

    // Local state for form management
    const [localTenant, setLocalTenant] = useState(tenant_id);
    const [localSite, setLocalSite] = useState(site_id);
    const [localGateway, setLocalGateway] = useState(gateway_id);
    const [isSaved, setIsSaved] = useState(false);

    // Sync local state if context changes externally (rare but good practice)
    useEffect(() => {
        setLocalTenant(tenant_id);
        setLocalSite(site_id);
        setLocalGateway(gateway_id);
    }, [tenant_id, site_id, gateway_id]);

    const handleSave = (e: React.FormEvent) => {
        e.preventDefault();
        updateConfig({
            tenant_id: localTenant,
            site_id: localSite,
            gateway_id: localGateway
        });

        // Brief visual feedback
        setIsSaved(true);
        setTimeout(() => setIsSaved(false), 2000);
    };

    // Optional: Fetch runtime defaults to show comparison or "Reset to Default"
    const { data: defaults, isLoading } = useQuery({
        queryKey: ['sticky-defaults'],
        queryFn: queries.getStickyDefaults
    });

    return (
        <div className="max-w-4xl mx-auto animate-in fade-in duration-500">
            <div className="mb-8">
                <h1 className="text-2xl font-bold tracking-tight text-white">Settings</h1>
                <p className="text-sm text-slate-400">Configure global application parameters.</p>
            </div>

            <div className="grid gap-8 md:grid-cols-2">
                {/* Configuration Form */}
                <div className="rounded-xl border border-white/10 bg-slate-950/50 p-6">
                    <h2 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                        <RefreshCw className="h-5 w-5 text-cyan-400" />
                        Environment Configuration
                    </h2>

                    <form onSubmit={handleSave} className="space-y-6">

                        {/* Demo Mode Toggle */}
                        <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 mb-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 className="font-medium text-indigo-400">Demo Mode</h3>
                                    <p className="text-xs text-indigo-300 mt-1">
                                        Use canned data to explore the application without a backend connection.
                                        Enabling/Disabling will reload the page.
                                    </p>
                                </div>
                                <Switch
                                    checked={localStorage.getItem('DEMO_MODE') === 'true'}
                                    onChange={() => {
                                        const isDemo = localStorage.getItem('DEMO_MODE') === 'true';
                                        if (isDemo) {
                                            localStorage.removeItem('DEMO_MODE');
                                        } else {
                                            localStorage.setItem('DEMO_MODE', 'true');
                                        }
                                        window.location.reload();
                                    }}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300">Tenant ID</label>
                            <input
                                type="text"
                                value={localTenant}
                                onChange={e => setLocalTenant(e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-mono"
                                placeholder="TENANT_01"
                            />
                            <p className="text-xs text-slate-500">The top-level organization identifier.</p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300">Site ID</label>
                            <input
                                type="text"
                                value={localSite}
                                onChange={e => setLocalSite(e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-mono"
                                placeholder="SITE_01"
                            />
                            <p className="text-xs text-slate-500">The specific physical location/site.</p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300">Gateway ID</label>
                            <input
                                type="text"
                                value={localGateway}
                                onChange={e => setLocalGateway(e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-mono"
                                placeholder="GW_001"
                            />
                            <p className="text-xs text-slate-500">The edge gateway identifier for this node.</p>
                        </div>

                        <div className="pt-4 flex items-center gap-4">
                            <button
                                type="submit"
                                className="flex items-center gap-2 rounded-lg bg-cyan-600 px-6 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20"
                            >
                                <Save className="h-4 w-4" />
                                {isSaved ? 'Saved!' : 'Save Changes'}
                            </button>
                            {isSaved && <span className="text-sm text-emerald-400 animate-in fade-in">Configuration updated successfully.</span>}
                        </div>
                    </form>
                </div>

                {/* Info / Debug Panel */}
                <div className="space-y-6">
                    <div className="rounded-xl border border-white/10 bg-slate-900/50 p-6">
                        <h3 className="text-sm font-medium text-slate-300 mb-4">Orchestrator Defaults</h3>
                        {isLoading ? (
                            <div className="text-sm text-slate-500">Loading backend defaults...</div>
                        ) : (
                            <div className="space-y-4 text-xs font-mono">
                                <div>
                                    <div className="text-slate-500 mb-1">Effective Defaults:</div>
                                    <div className="p-2 bg-black/30 rounded border border-white/5 text-emerald-400">
                                        {JSON.stringify(defaults?.effective_defaults, null, 2)}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-slate-500 mb-1">Last Used (Sticky):</div>
                                    <div className="p-2 bg-black/30 rounded border border-white/5 text-amber-400">
                                        {JSON.stringify(defaults?.last_used, null, 2)}
                                    </div>
                                </div>
                            </div>
                        )}
                        <p className="mt-4 text-xs text-slate-500">
                            These values are what the backend uses if no explicit IDs are sent.
                            Your local configuration overrides these for API requests.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
