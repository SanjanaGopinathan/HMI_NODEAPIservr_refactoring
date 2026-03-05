import { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Video, Filter, Plus, Search, Shield, Brain, Scan } from 'lucide-react';
import { queries, type Camera as CameraType } from '../../lib/api';
import { cn } from '../../lib/utils';
import { AddCameraModal } from './AddCameraModal';
import { ManageCameraModal } from './ManageCameraModal';
import { useConfig } from '../settings/ConfigContext';
import { VideoFloatingWindow } from '../../components/video/VideoFloatingWindow';

export function CamerasPage() {
    const { tenant_id, site_id, gateway_id } = useConfig();
    const [filter, setFilter] = useState('');
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isManageModalOpen, setIsManageModalOpen] = useState(false);
    const [selectedCamera, setSelectedCamera] = useState<CameraType | null>(null);
    const [activeStreamCamera, setActiveStreamCamera] = useState<CameraType | null>(null);

    // Fetch individual resources
    const { data: cameras = [], isLoading: camerasLoading, isError: camerasError } = useQuery({
        queryKey: ['cameras', tenant_id, site_id],
        queryFn: () => queries.listCameras({ tenant_id, site_id, gateway_id }),
    });

    const { data: models = [], isLoading: modelsLoading, isError: modelsError } = useQuery({
        queryKey: ['models', tenant_id, site_id],
        queryFn: () => queries.listModels({ tenant_id, site_id }),
    });

    const { data: policies = [], isLoading: policiesLoading, isError: policiesError } = useQuery({
        queryKey: ['policies', tenant_id, site_id],
        queryFn: () => queries.listPolicies({ tenant_id, site_id }),
    });

    const { data: profiles = [], isLoading: profilesLoading, isError: profilesError } = useQuery({
        queryKey: ['profiles', tenant_id, site_id],
        queryFn: () => queries.listProfiles({ tenant_id, site_id }),
    });

    const isLoading = camerasLoading || modelsLoading || policiesLoading || profilesLoading;
    const isError = camerasError || modelsError || policiesError || profilesError;


    const filteredCameras = cameras?.filter(cam =>
        cam.name.toLowerCase().includes(filter.toLowerCase()) ||
        cam.location.toLowerCase().includes(filter.toLowerCase())
    );

    const handleManage = (camera: CameraType) => {
        setSelectedCamera(camera);
        setIsManageModalOpen(true);
    };

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
            {/* Header Actions */}
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Cameras</h1>
                    <p className="text-sm text-slate-400">Manage surveillance cameras and their bindings.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Filter cameras..."
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="h-9 w-64 rounded-lg border border-white/10 bg-white/5 pl-9 pr-4 text-sm text-slate-200 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition-all"
                        />
                    </div>
                    <button className="flex items-center gap-2 rounded-lg bg-white/5 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-white/10 transition-colors border border-white/10">
                        <Filter className="h-4 w-4" />
                        Filters
                    </button>
                    <button
                        onClick={() => setIsAddModalOpen(true)}
                        className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20"
                    >
                        <Plus className="h-4 w-4" />
                        Add Camera
                    </button>
                    <AddCameraModal isOpen={isAddModalOpen} onClose={() => setIsAddModalOpen(false)} />
                    <ManageCameraModal
                        isOpen={isManageModalOpen}
                        onClose={() => { setIsManageModalOpen(false); setSelectedCamera(null); }}
                        camera={selectedCamera}
                    />
                </div>
            </div>

            {/* Camera Grid */}
            {isLoading ? (
                <div className="flex h-64 items-center justify-center text-slate-500">Loading cameras...</div>
            ) : isError ? (
                <div className="flex h-64 items-center justify-center text-rose-500">Failed to load cameras</div>
            ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {(() => {
                        const safeCameras = Array.isArray(filteredCameras) ? filteredCameras : [];

                        if (safeCameras.length === 0) {
                            return <div className="col-span-full text-center text-slate-500 py-12">No cameras found matching your filter.</div>;
                        }

                        return safeCameras.map((camera) => (
                            <CameraGridItem
                                key={camera.id}
                                camera={camera}
                                onManage={handleManage}
                                onPlay={() => setActiveStreamCamera(camera)}
                                tenant_id={tenant_id || ''}
                                site_id={site_id || ''}
                                gateway_id={gateway_id || ''}
                                models={models}
                                policies={policies}
                                profiles={profiles}
                            />
                        ));
                    })()}
                </div>
            )}

            {/* Video Floating Window */}
            {activeStreamCamera && (
                <VideoFloatingWindow
                    camera={activeStreamCamera}
                    onClose={() => setActiveStreamCamera(null)}
                />
            )}
        </div>
    );
}

function CameraGridItem({
    camera,
    onManage,
    onPlay,
    tenant_id,
    site_id,
    gateway_id,
    models,
    policies,
    profiles
}: {
    camera: CameraType,
    onManage: (c: CameraType) => void,
    onPlay: (c: CameraType) => void,
    tenant_id: string,
    site_id: string,
    gateway_id: string,
    models: any[],
    policies: any[],
    profiles: any[]
}) {
    const [isToggling, setIsToggling] = useState(false);
    const queryClient = useQueryClient();

    const handleToggle = async (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();

        setIsToggling(true);
        try {
            // Fix for _id vs id and lint issues
            const camId = camera.id || (camera as any)._id;

            if (camera.status === 'ACTIVE') {
                await queries.disablePPE(camId, { tenant_id, site_id, gateway_id });
            } else {
                await queries.enablePPE(camId, { tenant_id, site_id, gateway_id });
            }
            queryClient.invalidateQueries({ queryKey: ['cameras'] });
            queryClient.invalidateQueries({ queryKey: ['siteHealth'] });
        } catch (error) {
            console.error("Failed to toggle camera:", error);
            alert("Failed to toggle camera status.");
        } finally {
            setIsToggling(false);
        }
    };

    // Lookup details
    // The backend stores assignments in asset_info.bindings
    const bindings = (camera as any).asset_info?.bindings || {};
    const modelId = bindings.assigned_model_id || (camera as any).assigned_model_id;
    const policyId = bindings.assigned_policy_id || (camera as any).assigned_policy_id;
    const profileIds = bindings.target_profile_ids || (camera as any).target_profile_ids || [];

    const assignedModel = models.find((m: any) =>
        modelId && (m.id === modelId || m._id === modelId)
    );
    const assignedPolicy = policies.find((p: any) =>
        policyId && (p.id === policyId || p._id === policyId)
    );

    // Map profile IDs to profile objects
    const assignedProfiles = profileIds.map((pid: string) =>
        profiles.find((p: any) => p.id === pid || p._id === pid)
    ).filter(Boolean);

    return (
        <div className="group relative flex flex-col rounded-xl border border-white/10 bg-slate-950/50 p-4 transition-all hover:bg-white/5">
            <div className="mb-4 flex items-start justify-between">
                <div
                    onClick={() => camera.status === 'ACTIVE' && onPlay(camera)}
                    className={cn(
                        "rounded-lg p-2 transition-colors",
                        camera.status === 'ACTIVE'
                            ? "bg-slate-800 text-slate-400 group-hover:bg-cyan-500/10 group-hover:text-cyan-400 cursor-pointer hover:shadow-lg hover:shadow-cyan-500/20"
                            : "bg-slate-900 text-slate-600 cursor-not-allowed"
                    )}
                    title={camera.status === 'ACTIVE' ? "Click to view stream" : "Enable camera to view stream"}
                >
                    <Video className="h-6 w-6" />
                </div>

                {/* Toggle Button */}
                <button
                    onClick={handleToggle}
                    disabled={isToggling}
                    className={cn(
                        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 border-0",
                        camera.status === 'ACTIVE' ? 'bg-emerald-500' : 'bg-slate-700',
                        isToggling ? 'opacity-50 cursor-wait' : 'cursor-pointer'
                    )}
                    title={camera.status === 'ACTIVE' ? "Disable PPE" : "Enable PPE"}
                >
                    <span
                        className={cn(
                            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                            camera.status === 'ACTIVE' ? 'translate-x-6' : 'translate-x-1'
                        )}
                    />
                </button>
            </div>

            <div className="mb-4 flex-1">
                <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors truncate max-w-[70%]">{camera.name}</h3>
                    <span className={cn(
                        "text-[10px] font-bold",
                        camera.status === 'ACTIVE' ? 'text-emerald-400' : 'text-slate-500'
                    )}>
                        {isToggling ? 'UPDATING...' : camera.status}
                    </span>
                </div>
                <p className="text-sm text-slate-500 truncate">{camera.location || 'No location set'}</p>

            </div>

            <div className="flex items-center justify-between border-t border-white/5 pt-4">
                <div className="flex gap-2">
                    {/* Model Icon with Tooltip */}
                    <div className="group/tooltip relative flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors cursor-pointer">
                        <Brain className="h-4 w-4" />
                        {/* Tooltip */}
                        <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] opacity-0 group-hover/tooltip:opacity-100 transition-opacity z-50">
                            <div className="bg-slate-900 text-xs rounded-md shadow-xl border border-white/10 p-2 text-slate-200">
                                <p className="font-semibold text-cyan-400 mb-1 border-b border-white/5 pb-1">Model Config</p>
                                {assignedModel ? (
                                    <>
                                        <p className="font-medium">{assignedModel.name}</p>
                                        <p className="text-[10px] text-slate-500 capitalize mt-0.5">{assignedModel.framework_id}</p>
                                    </>
                                ) : (
                                    <p className="text-slate-500 italic">No model assigned</p>
                                )}
                            </div>
                            {/* Arrow */}
                            <div className="w-2 h-2 bg-slate-900 border-r border-b border-white/10 transform rotate-45 absolute left-1/2 -translate-x-1/2 -bottom-1"></div>
                        </div>
                    </div>

                    {/* Policy Icon with Tooltip */}
                    <div className="group/tooltip relative flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors cursor-pointer">
                        <Shield className="h-4 w-4" />
                        {/* Tooltip */}
                        <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] opacity-0 group-hover/tooltip:opacity-100 transition-opacity z-50">
                            <div className="bg-slate-900 text-xs rounded-md shadow-xl border border-white/10 p-2 text-slate-200">
                                <p className="font-semibold text-cyan-400 mb-1 border-b border-white/5 pb-1">Alert Policy</p>
                                {assignedPolicy ? (
                                    <>
                                        <p className="font-medium">{assignedPolicy.anomaly_type?.replace(/_/g, ' ')}</p>
                                        <p className="text-[10px] text-slate-500 mt-0.5">Min Severity: <span className="text-slate-300">{assignedPolicy.min_severity}</span></p>
                                    </>
                                ) : (
                                    <p className="text-slate-500 italic">No policy assigned</p>
                                )}
                            </div>
                            {/* Arrow */}
                            <div className="w-2 h-2 bg-slate-900 border-r border-b border-white/10 transform rotate-45 absolute left-1/2 -translate-x-1/2 -bottom-1"></div>
                        </div>
                    </div>

                    {/* Profile Icon with Tooltip */}
                    <div className="group/tooltip relative flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors cursor-pointer">
                        <Scan className="h-4 w-4" />
                        {/* Tooltip */}
                        <div className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[200px] opacity-0 group-hover/tooltip:opacity-100 transition-opacity z-50">
                            <div className="bg-slate-900 text-xs rounded-md shadow-xl border border-white/10 p-2 text-slate-200">
                                <p className="font-semibold text-cyan-400 mb-1 border-b border-white/5 pb-1">Detection Profile</p>
                                {assignedProfiles.length > 0 ? (
                                    <div className="flex flex-col gap-1">
                                        {assignedProfiles.map((p: any) => (
                                            <div key={p.id || p._id} className="flex flex-col">
                                                <span className="font-medium">{p.name}</span>
                                                <span className="text-[10px] text-slate-500">
                                                    Targets: {p.targets?.join(', ') || 'None'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-slate-500 italic">No profiles assigned</p>
                                )}
                            </div>
                            {/* Arrow */}
                            <div className="w-2 h-2 bg-slate-900 border-r border-b border-white/10 transform rotate-45 absolute left-1/2 -translate-x-1/2 -bottom-1"></div>
                        </div>
                    </div>
                </div>
                <button
                    onClick={() => onManage(camera)}
                    className="text-xs font-medium text-cyan-500 hover:text-cyan-400 transition-colors"
                >
                    Manage
                </button>
            </div>
        </div>
    );
}
