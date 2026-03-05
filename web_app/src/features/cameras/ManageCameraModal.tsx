import { Fragment, useState, useEffect } from 'react';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import { X, Save, AlertCircle } from 'lucide-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { queries, type Camera } from '../../lib/api';
import { useConfig } from '../settings/ConfigContext';

interface ManageCameraModalProps {
    isOpen: boolean;
    onClose: () => void;
    camera: Camera | null;
}

export function ManageCameraModal({ isOpen, onClose, camera }: ManageCameraModalProps) {
    const { tenant_id, site_id } = useConfig();
    const queryClient = useQueryClient();

    const [assignedModelId, setAssignedModelId] = useState('');
    const [assignedPolicyId, setAssignedPolicyId] = useState('');
    const [targetProfileIds, setTargetProfileIds] = useState<string[]>([]);

    // Fetch available resources
    const { data: models } = useQuery({ queryKey: ['models', tenant_id, site_id], queryFn: () => queries.listModels({ tenant_id, site_id }) });
    const { data: policies } = useQuery({ queryKey: ['policies', tenant_id, site_id], queryFn: () => queries.listPolicies({ tenant_id, site_id }) });
    const { data: profiles } = useQuery({ queryKey: ['profiles', tenant_id, site_id], queryFn: () => queries.listProfiles({ tenant_id, site_id }) });

    // Load initial state when camera changes
    useEffect(() => {
        if (camera) {
            // Since the listCameras endpoint currently returns a flat structure (mostly), 
            // we might need to fetch full context or rely on what's available.
            // For now, assuming these fields might be present or we default to empty.
            // In a real scenario, we'd probably want to call queries.getCameraFullContext(camera.id) here.
            // But to keep it snappy, let's start with defaults or try to read from camera object if extended.

            // Allow user to set fresh logic
            setAssignedModelId('');
            setAssignedPolicyId('');
            setTargetProfileIds([]);

            // Note: To pre-fill, we would need the camera object to contain these bindings. 
            // The current Camera interface in api.ts is minimal. 
            // Let's assume for this "Assign" workflow, starting fresh is acceptable 
            // OR we fetch context. Let's fetch context for better UX.
        }
    }, [camera]);

    // Fetch specific bindings for this camera when opening
    const { data: fullContext } = useQuery({
        queryKey: ['camera-context', camera?.id, tenant_id, site_id],
        queryFn: () => camera ? queries.getCameraFullContext(camera.id, { tenant_id, site_id }) : null,
        enabled: !!camera && isOpen,
    });

    // Update local state when context loads
    useEffect(() => {
        if (fullContext?.camera?.asset_info?.bindings) {
            const bindings = fullContext.camera.asset_info.bindings;
            setAssignedModelId(bindings.assigned_model_id || '');
            setAssignedPolicyId(bindings.assigned_policy_id || '');
            setTargetProfileIds(bindings.target_profile_ids || []);
        }
    }, [fullContext]);


    const mutation = useMutation({
        mutationFn: queries.updateCamera,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cameras'] });
            queryClient.invalidateQueries({ queryKey: ['camera-context', camera?.id] });
            onClose();
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!camera) return;

        mutation.mutate({
            camera_id: camera.id,
            assigned_model_id: assignedModelId || undefined,
            assigned_policy_id: assignedPolicyId || undefined,
            target_profile_ids: targetProfileIds.length > 0 ? targetProfileIds : undefined,
        });
    };

    const toggleProfile = (profileId: string) => {
        setTargetProfileIds(prev =>
            prev.includes(profileId)
                ? prev.filter(id => id !== profileId)
                : [...prev, profileId]
        );
    };

    return (
        <Transition show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <TransitionChild
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" />
                </TransitionChild>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4 text-center">
                        <TransitionChild
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <DialogPanel className="w-full max-w-lg transform overflow-hidden rounded-2xl border border-white/10 bg-slate-900 p-6 text-left align-middle shadow-xl transition-all">
                                <div className="flex items-center justify-between mb-6">
                                    <DialogTitle as="h3" className="text-xl font-semibold leading-6 text-white">
                                        Manage Camera: <span className="text-cyan-400">{camera?.name}</span>
                                    </DialogTitle>
                                    <button onClick={onClose} className="rounded-full p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors">
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <form onSubmit={handleSubmit} className="flex flex-col gap-6">

                                    {/* AI Model Selection */}
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-300">Assigned AI Model</label>
                                        <select
                                            value={assignedModelId}
                                            onChange={(e) => setAssignedModelId(e.target.value)}
                                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                        >
                                            <option value="" className="bg-slate-900 text-slate-300">Select a Model...</option>
                                            {Array.isArray(models) && models.map((model: any) => (
                                                <option key={model._id} value={model._id} className="bg-slate-900 text-slate-100">
                                                    {model.name} ({model.framework})
                                                </option>
                                            ))}
                                        </select>
                                        <p className="text-xs text-slate-500">The AI model responsible for processing video feeds.</p>
                                    </div>

                                    {/* Detection Customization (Profiles) */}
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-300">Detection Profiles</label>
                                        <div className="max-h-32 overflow-y-auto rounded-lg border border-white/10 bg-white/5 p-2 space-y-1">
                                            {Array.isArray(profiles) ? profiles.map((profile: any) => (
                                                <div
                                                    key={profile._id}
                                                    onClick={() => toggleProfile(profile._id)}
                                                    className={`flex items-center gap-3 p-2 rounded cursor-pointer transition-colors ${targetProfileIds.includes(profile._id) ? 'bg-cyan-500/20 text-cyan-200' : 'hover:bg-white/5 text-slate-400'}`}
                                                >
                                                    <div className={`w-4 h-4 rounded border flex items-center justify-center ${targetProfileIds.includes(profile._id) ? 'border-cyan-500 bg-cyan-500' : 'border-slate-600'}`}>
                                                        {targetProfileIds.includes(profile._id) && <span className="text-white text-xs">✓</span>}
                                                    </div>
                                                    <span className="text-sm">{profile.name}</span>
                                                </div>
                                            )) : (
                                                <div className="p-2 text-xs text-slate-500 italic">No profiles available (or failed to load)</div>
                                            )}
                                        </div>
                                        <p className="text-xs text-slate-500">Select which objects to detect (e.g., Helmet, Vest, Person).</p>
                                    </div>


                                    {/* Alert Policy Selection */}
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium text-slate-300">Alert Policy</label>
                                        <select
                                            value={assignedPolicyId}
                                            onChange={(e) => setAssignedPolicyId(e.target.value)}
                                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                        >
                                            <option value="" className="bg-slate-900 text-slate-300">Select a Policy...</option>
                                            {Array.isArray(policies) && policies.map((policy: any) => (
                                                <option key={policy._id} value={policy._id} className="bg-slate-900 text-slate-100">
                                                    {policy.anomaly_type} ({policy.priority} - {policy.enabled ? 'On' : 'Off'})
                                                </option>
                                            ))}
                                        </select>
                                        <p className="text-xs text-slate-500">Determines who gets notified and how.</p>
                                    </div>

                                    <div className="mt-4 flex justify-end gap-3 pt-4 border-t border-white/5">
                                        <button
                                            type="button"
                                            onClick={onClose}
                                            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/5 hover:text-white transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={mutation.isPending}
                                            className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            <Save className="h-4 w-4" />
                                            {mutation.isPending ? 'Saving...' : 'Save Configuration'}
                                        </button>
                                    </div>
                                    {mutation.isError && (
                                        <div className="flex items-center gap-2 text-sm text-rose-500 bg-rose-500/10 p-3 rounded-lg border border-rose-500/20">
                                            <AlertCircle className="h-4 w-4" />
                                            <span>Error updating camera: {mutation.error.message}</span>
                                        </div>
                                    )}
                                </form>
                            </DialogPanel>
                        </TransitionChild>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
