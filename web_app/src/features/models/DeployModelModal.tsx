import { Fragment, useState, useMemo } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { X, Search, Check, AlertCircle, Camera } from 'lucide-react';
import { queries } from '../../lib/api';
import { useConfig } from '../settings/ConfigContext';
import { cn } from '../../lib/utils';

interface DeployModelModalProps {
    isOpen: boolean;
    onClose: () => void;
    model: any;
}

export function DeployModelModal({ isOpen, onClose, model }: DeployModelModalProps) {
    const { tenant_id, site_id, gateway_id } = useConfig();
    const queryClient = useQueryClient();
    const [selectedCameras, setSelectedCameras] = useState<Set<string>>(new Set());
    const [filter, setFilter] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Fetch all cameras
    const { data: cameras = [], isLoading } = useQuery({
        queryKey: ['cameras', tenant_id, site_id],
        queryFn: () => queries.listCameras({ tenant_id, site_id }),
        enabled: isOpen,
    });

    // Filter cameras
    const filteredCameras = useMemo(() => {
        return cameras.filter(cam => {
            const matchesFilter =
                cam.name.toLowerCase().includes(filter.toLowerCase()) ||
                cam.location?.toLowerCase().includes(filter.toLowerCase()) ||
                cam.id.toLowerCase().includes(filter.toLowerCase());

            // Should verify if camera supports this model? 
            // For now, list all cameras that don't already have this model assigned
            const isNotAssigned = (cam as any).asset_info?.bindings?.assigned_model_id !== model?._id;

            return matchesFilter && isNotAssigned;
        });
    }, [cameras, filter, model]);

    const toggleCamera = (cameraId: string) => {
        const newSelected = new Set(selectedCameras);
        if (newSelected.has(cameraId)) {
            newSelected.delete(cameraId);
        } else {
            newSelected.add(cameraId);
        }
        setSelectedCameras(newSelected);
    };

    const handleDeploy = async () => {
        if (!model) return;
        setIsSubmitting(true);
        setError(null);

        try {
            await queries.assignCamerasToModel({
                tenant_id,
                site_id,
                gateway_id,
                model_id: model._id,
                camera_ids: Array.from(selectedCameras)
            });

            // Success
            queryClient.invalidateQueries({ queryKey: ['cameras'] });
            // Maybe show toast?
            onClose();
            setSelectedCameras(new Set());
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || 'Failed to deploy model');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!model) return null;

    return (
        <Transition appear show={isOpen} as={Fragment}>
            <Dialog as="div" className="relative z-50" onClose={onClose}>
                <Transition.Child
                    as={Fragment}
                    enter="ease-out duration-300"
                    enterFrom="opacity-0"
                    enterTo="opacity-100"
                    leave="ease-in duration-200"
                    leaveFrom="opacity-100"
                    leaveTo="opacity-0"
                >
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" />
                </Transition.Child>

                <div className="fixed inset-0 overflow-y-auto">
                    <div className="flex min-h-full items-center justify-center p-4 text-center">
                        <Transition.Child
                            as={Fragment}
                            enter="ease-out duration-300"
                            enterFrom="opacity-0 scale-95"
                            enterTo="opacity-100 scale-100"
                            leave="ease-in duration-200"
                            leaveFrom="opacity-100 scale-100"
                            leaveTo="opacity-0 scale-95"
                        >
                            <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-slate-900 border border-white/10 p-6 text-left align-middle shadow-xl transition-all flex flex-col max-h-[80vh]">
                                <div className="flex items-center justify-between mb-4 flex-shrink-0">
                                    <div>
                                        <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-white">
                                            Deploy Model
                                        </Dialog.Title>
                                        <p className="text-sm text-slate-400">
                                            Select cameras to deploy <span className="text-cyan-400 font-medium">{model.name}</span> to.
                                        </p>
                                    </div>
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                {error && (
                                    <div className="mb-4 rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 flex items-center gap-2 text-sm text-rose-400 flex-shrink-0">
                                        <AlertCircle className="h-4 w-4" />
                                        {error}
                                    </div>
                                )}

                                <div className="mb-4 flex-shrink-0">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                                        <input
                                            type="text"
                                            placeholder="Search cameras..."
                                            value={filter}
                                            onChange={(e) => setFilter(e.target.value)}
                                            className="w-full rounded-lg border border-white/10 bg-white/5 pl-9 pr-4 py-2 text-sm text-slate-200 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                        />
                                    </div>
                                </div>

                                <div className="flex-1 overflow-y-auto pr-2 space-y-2 min-h-[300px]">
                                    {isLoading ? (
                                        <div className="flex h-32 items-center justify-center text-slate-500">
                                            Loading cameras...
                                        </div>
                                    ) : filteredCameras.length === 0 ? (
                                        <div className="flex h-32 items-center justify-center text-slate-500 border border-dashed border-white/10 rounded-lg">
                                            No cameras found
                                        </div>
                                    ) : (
                                        filteredCameras.map((cam: any) => {
                                            const isSelected = selectedCameras.has(cam.id);
                                            const currentModel = cam.asset_info?.bindings?.assigned_model_id;

                                            return (
                                                <div
                                                    key={cam.id}
                                                    onClick={() => toggleCamera(cam.id)}
                                                    className={cn(
                                                        "flex items-center justify-between p-3 rounded-lg border cursor-pointer transition-all",
                                                        isSelected
                                                            ? "bg-cyan-500/10 border-cyan-500/50"
                                                            : "bg-white/5 border-white/5 hover:bg-white/10"
                                                    )}
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div className={cn(
                                                            "h-10 w-10 rounded-lg flex items-center justify-center",
                                                            isSelected ? "bg-cyan-500/20 text-cyan-400" : "bg-slate-800 text-slate-400"
                                                        )}>
                                                            <Camera className="h-5 w-5" />
                                                        </div>
                                                        <div>
                                                            <h4 className={cn("text-sm font-medium", isSelected ? "text-cyan-100" : "text-slate-200")}>
                                                                {cam.name}
                                                            </h4>
                                                            <p className="text-xs text-slate-500 flex items-center gap-1">
                                                                {cam.location || "Unknown Location"}
                                                                {currentModel && (
                                                                    <span className="text-amber-500 ml-2">• Currently: {currentModel}</span>
                                                                )}
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <div className={cn(
                                                        "h-5 w-5 rounded-full border flex items-center justify-center transition-colors",
                                                        isSelected
                                                            ? "bg-cyan-500 border-cyan-500 text-white"
                                                            : "border-slate-600"
                                                    )}>
                                                        {isSelected && <Check className="h-3 w-3" />}
                                                    </div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>

                                <div className="flex items-center justify-between pt-4 border-t border-white/5 mt-4 flex-shrink-0">
                                    <div className="text-sm text-slate-400">
                                        {selectedCameras.size} cameras selected
                                    </div>
                                    <div className="flex gap-3">
                                        <button
                                            onClick={onClose}
                                            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={handleDeploy}
                                            disabled={selectedCameras.size === 0 || isSubmitting}
                                            className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {isSubmitting ? 'Deploying...' : 'Deploy to Selected'}
                                        </button>
                                    </div>
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
