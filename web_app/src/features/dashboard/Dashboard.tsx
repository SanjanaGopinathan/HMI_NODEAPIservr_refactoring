import { useState, useEffect } from 'react';
import { Activity, AlertTriangle, Cloud, Server, Video, AlertCircle } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { queries } from '../../lib/api';
import { useConfig } from '../settings/ConfigContext';
import { Link } from 'react-router-dom';
import { ViewIssuesModal } from './ViewIssuesModal';

// Internal Camera Card Component to handle individual state logic
function CameraCard({ camera, tenant_id, site_id, gateway_id }: { camera: any, tenant_id: string, site_id: string, gateway_id: string }) {
    const [isToggling, setIsToggling] = useState(false);
    const queryClient = useQueryClient();

    const handleToggle = async (e: React.MouseEvent) => {
        e.preventDefault(); // Prevent navigation link
        e.stopPropagation();

        setIsToggling(true);
        try {
            if (camera.status === 'ACTIVE') {
                await queries.disablePPE(camera.id || camera._id, { tenant_id, site_id, gateway_id });
            } else {
                await queries.enablePPE(camera.id || camera._id, { tenant_id, site_id, gateway_id });
            }
            // Invalidate to refresh list
            queryClient.invalidateQueries({ queryKey: ['cameras'] });
            queryClient.invalidateQueries({ queryKey: ['siteHealth'] });
        } catch (error) {
            console.error("Failed to toggle camera:", error);
            alert("Failed to toggle camera status. See console.");
        } finally {
            setIsToggling(false);
        }
    };

    return (
        <Link
            to={`/cameras?highlight=${camera.id || camera._id}`}
            className="block p-4 rounded-lg bg-slate-900 border border-white/5 hover:border-cyan-500/30 transition-all group relative"
        >
            <div className="flex justify-between items-start mb-2">
                <div className="p-2 rounded bg-slate-800 text-slate-400 group-hover:text-cyan-400 transition-colors">
                    <Video className="h-5 w-5" />
                </div>

                {/* Toggle Button */}
                <button
                    onClick={handleToggle}
                    disabled={isToggling}
                    className={`
                        relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 border-0
                        ${camera.status === 'ACTIVE' ? 'bg-emerald-500' : 'bg-slate-700'}
                        ${isToggling ? 'opacity-50 cursor-wait' : 'cursor-pointer'}
                    `}
                    title={camera.status === 'ACTIVE' ? "Disable PPE" : "Enable PPE"}
                >
                    <span
                        className={`
                            inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                            ${camera.status === 'ACTIVE' ? 'translate-x-6' : 'translate-x-1'}
                        `}
                    />
                </button>
            </div>

            <h4 className="text-sm font-medium text-slate-200 truncate" title={camera.name}>{camera.name}</h4>

            <div className="flex justify-between items-center mt-1">
                <p className="text-xs text-slate-500 truncate max-w-[60%]">{camera.location || 'Unknown Location'}</p>
                <span className={`text-[10px] font-bold ${camera.status === 'ACTIVE' ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {isToggling ? 'UPDATING...' : camera.status}
                </span>
            </div>
        </Link>
    );
}

export function Dashboard() {
    const { tenant_id, site_id, updateConfig } = useConfig();
    const [selectedGatewayId, setSelectedGatewayId] = useState<string | null>(null);
    const [isIssuesModalOpen, setIsIssuesModalOpen] = useState(false);

    // 1. Fetch Site Health (Top Stats)
    const { data: health, isLoading: isHealthLoading } = useQuery({
        queryKey: ['siteHealth', tenant_id, site_id],
        queryFn: () => queries.getSiteHealth({ tenant_id, site_id }),
        refetchInterval: 30000,
    });

    // 2. Fetch Gateways (Master List)
    const { data: gateways = [], isLoading: isGatewaysLoading } = useQuery({
        queryKey: ['gateways', tenant_id, site_id],
        queryFn: () => queries.listGateways({ tenant_id, site_id }),
    });

    // 3. Select first gateway by default when loaded
    useEffect(() => {
        if (gateways.length > 0 && !selectedGatewayId) {
            const firstGw = gateways[0];
            const newId = firstGw._id;
            setSelectedGatewayId(newId);
            updateConfig({ gateway_id: newId });
            queries.configureMapper(newId).catch(e => console.error("Failed to auto-configure mapper:", e));
        }
    }, [gateways]);

    // 4. Fetch Cameras for Selected Gateway (Detail View)
    const { data: cameras = [], isLoading: isCamerasLoading } = useQuery({
        queryKey: ['cameras', tenant_id, site_id, selectedGatewayId],
        queryFn: () => selectedGatewayId ? queries.listCameras({ tenant_id, site_id, gateway_id: selectedGatewayId }) : [],
        enabled: !!selectedGatewayId,
    });

    if (isHealthLoading || isGatewaysLoading) return <div className="flex h-full items-center justify-center text-slate-500">Loading dashboard...</div>;

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
            <ViewIssuesModal
                isOpen={isIssuesModalOpen}
                onClose={() => setIsIssuesModalOpen(false)}
                issues={health?.issues || []}
            />

            {/* --- Top Stats Section --- */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {/* ... (first two panels remain unchanged) */}
                <div className="glass-panel rounded-xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Activity className="h-16 w-16 text-cyan-500" />
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
                            <Activity className="h-5 w-5" />
                        </div>
                        <span className="text-sm font-medium text-slate-400">Site Health Score</span>
                    </div>
                    <div className="mt-3 flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-slate-100">{health?.health_score ?? 0}%</span>
                    </div>
                </div>

                <div className="glass-panel rounded-xl p-5 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Video className="h-16 w-16 text-blue-500" />
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-blue-500/10 p-2 text-blue-400">
                            <Video className="h-5 w-5" />
                        </div>
                        <span className="text-sm font-medium text-slate-400">Total Cameras</span>
                    </div>
                    <div className="mt-3 flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-slate-100">
                            {(health?.cameras_active ?? 0) + (health?.cameras_inactive ?? 0)}
                        </span>
                        <span className="text-xs font-medium text-slate-500">
                            ({health?.cameras_active ?? 0} active)
                        </span>
                    </div>
                </div>

                <div
                    onClick={() => setIsIssuesModalOpen(true)}
                    className="glass-panel rounded-xl p-5 relative overflow-hidden group cursor-pointer hover:border-rose-500/30 transition-all active:scale-[0.99]"
                >
                    <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                        <AlertTriangle className="h-16 w-16 text-rose-500" />
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="rounded-lg bg-rose-500/10 p-2 text-rose-400">
                            <AlertTriangle className="h-5 w-5" />
                        </div>
                        <span className="text-sm font-medium text-slate-400">Issues</span>
                    </div>
                    <div className="mt-3 flex items-baseline gap-2">
                        <span className="text-2xl font-bold text-slate-100">{health?.issues.length ?? 0}</span>
                        <span className="text-xs font-medium text-rose-400">Require Attention</span>
                    </div>
                </div>
            </div>

            {/* --- Gateway Master-Detail View --- */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-[500px]">

                {/* Master: Gateway List */}
                <div className="lg:col-span-4 glass-panel rounded-xl p-0 overflow-hidden flex flex-col">
                    <div className="p-4 border-b border-white/5 bg-slate-900/50">
                        <h3 className="flex items-center gap-2 text-lg font-medium text-slate-200">
                            <Server className="h-5 w-5 text-cyan-400" />
                            Gateways
                        </h3>
                    </div>
                    <div className="flex-1 overflow-y-auto space-y-1 p-2 scrollbar-thin scrollbar-thumb-white/10">
                        {gateways.length > 0 ? gateways.map((gw: any) => (
                            <div
                                key={gw._id}
                                onClick={() => {
                                    setSelectedGatewayId(gw._id);
                                    updateConfig({ gateway_id: gw._id });
                                    queries.configureMapper(gw._id).catch(e => console.error("Failed to configure mapper:", e));
                                }}
                                className={`p-3 rounded-lg cursor-pointer transition-all border ${selectedGatewayId === gw._id ? 'bg-cyan-500/10 border-cyan-500/50' : 'bg-transparent border-transparent hover:bg-white/5'}`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className={`font-medium ${selectedGatewayId === gw._id ? 'text-cyan-400' : 'text-slate-300'}`}>
                                        {gw.name}
                                    </span>
                                    {gw.status === 'ONLINE' ? (
                                        <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span>
                                    ) : (
                                        <span className="h-2 w-2 rounded-full bg-rose-500"></span>
                                    )}
                                </div>
                                <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                                    <Cloud className="h-3 w-3" />
                                    <span>{gw._id}</span>
                                </div>
                            </div>
                        )) : (
                            <div className="p-4 text-center text-slate-500 text-sm">No gateways found.</div>
                        )}
                    </div>
                </div>

                {/* Detail: Gateway Details & Assets */}
                <div className="lg:col-span-8 flex flex-col gap-6">

                    {/* Gateway Details Card */}
                    {selectedGatewayId && (() => {
                        const gw = gateways.find((g: any) => g._id === selectedGatewayId);
                        if (!gw) return null;
                        return (
                            <div className="glass-panel rounded-xl p-5 border-l-4 border-l-cyan-500">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h3 className="text-xl font-semibold text-slate-100 flex items-center gap-2">
                                            {gw.name}
                                            <span className="text-xs font-normal text-slate-500 px-2 py-0.5 rounded bg-white/5 border border-white/5">
                                                {gw._id}
                                            </span>
                                        </h3>
                                        <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-400">
                                            <div className="flex items-center gap-1.5">
                                                <Cloud className="h-3.5 w-3.5" />
                                                <span>IP: {gw.hmi?.base_url?.replace('http://', '')?.replace('https://', '') || 'N/A'}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <Activity className="h-3.5 w-3.5" />
                                                <span>Last Seen: {gw.last_seen_at ? new Date(gw.last_seen_at).toLocaleString() : 'Never'}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${gw.status === 'ONLINE' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/20 text-rose-400 border border-rose-500/20'}`}>
                                            <span className={`h-1.5 w-1.5 rounded-full ${gw.status === 'ONLINE' ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
                                            {gw.status}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })()}

                    {/* Assets Grid */}
                    <div className="glass-panel rounded-xl p-0 overflow-hidden flex flex-col flex-1">
                        <div className="p-4 border-b border-white/5 bg-slate-900/50 flex justify-between items-center">
                            <h3 className="flex items-center gap-2 text-lg font-medium text-slate-200">
                                <Video className="h-5 w-5 text-indigo-400" />
                                Connected Assets
                            </h3>
                        </div>

                        <div className="flex-1 p-4 bg-slate-950/30">
                            {selectedGatewayId ? (
                                isCamerasLoading ? (
                                    <div className="h-full flex items-center justify-center text-slate-500">Loading assets...</div>
                                ) : cameras.length > 0 ? (
                                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                        {cameras.map((cam: any) => (
                                            <CameraCard
                                                key={cam.id}
                                                camera={cam}
                                                tenant_id={tenant_id}
                                                site_id={site_id}
                                                gateway_id={selectedGatewayId}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-2">
                                        <Video className="h-8 w-8 opacity-20" />
                                        <span>No assets found for this gateway.</span>
                                    </div>
                                )
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-2 opacity-50">
                                    <Server className="h-8 w-8" />
                                    <span>Select a gateway to view assets.</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* --- Bottom: Recommendations --- */}
            <div className="glass-panel rounded-xl p-6">
                <h3 className="flex items-center gap-2 text-lg font-medium text-slate-200 mb-4">
                    <AlertCircle className="h-5 w-5 text-amber-500" />
                    System Recommendations
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {health?.recommendations && health.recommendations.length > 0 ? health.recommendations.map((rec: string, i: number) => (
                        <div key={i} className="flex gap-3 rounded-lg border border-amber-500/20 bg-amber-500/5 p-3">
                            <div className="mt-1 h-2 w-2 rounded-full bg-amber-500 shrink-0" />
                            <p className="text-sm text-slate-300">{rec}</p>
                        </div>
                    )) : (
                        <div className="text-sm text-slate-500 italic p-2">All systems optimal. No recommendations.</div>
                    )}
                </div>
            </div>
        </div>
    );
}
