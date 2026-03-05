import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, Brain, Hash, Layers } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ModelDetailsModalProps {
    isOpen: boolean;
    onClose: () => void;
    model: any;
}

export function ModelDetailsModal({ isOpen, onClose, model }: ModelDetailsModalProps) {
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
                            <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-slate-900 border border-white/10 p-6 text-left align-middle shadow-xl transition-all">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3">
                                        <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
                                            <Brain className="h-6 w-6" />
                                        </div>
                                        <div>
                                            <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-white">
                                                {model.name}
                                            </Dialog.Title>
                                            <p className="text-sm text-slate-400">{model.framework_id}</p>
                                        </div>
                                    </div>
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <div className="space-y-6">
                                    {/* Status Section */}
                                    <div className="rounded-xl bg-white/5 p-4 border border-white/5">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-slate-400">Status</span>
                                            <div className={cn(
                                                "flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium border",
                                                model.status === 'ACTIVE'
                                                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                                    : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                                            )}>
                                                <span className={cn("h-1.5 w-1.5 rounded-full", model.status === 'ACTIVE' ? "bg-emerald-500" : "bg-slate-500")} />
                                                {model.status}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Identifiers */}
                                    <div className="space-y-4">
                                        <h4 className="flex items-center gap-2 text-sm font-medium text-white">
                                            <Hash className="h-4 w-4 text-cyan-400" />
                                            Identifiers
                                        </h4>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="rounded-lg bg-slate-950 p-3">
                                                <p className="text-xs text-slate-500 mb-1">Model ID</p>
                                                <p className="text-sm text-slate-200 font-mono truncate" title={model._id}>{model._id}</p>
                                            </div>
                                            <div className="rounded-lg bg-slate-950 p-3">
                                                <p className="text-xs text-slate-500 mb-1">Framework ID</p>
                                                <p className="text-sm text-slate-200 font-mono truncate" title={model.framework_id}>{model.framework_id}</p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Supported Profiles */}
                                    <div className="space-y-4">
                                        <h4 className="flex items-center gap-2 text-sm font-medium text-white">
                                            <Layers className="h-4 w-4 text-purple-400" />
                                            Supported Profiles
                                        </h4>
                                        <div className="flex flex-wrap gap-2">
                                            {model.Supported_Profile_ids?.length > 0 ? (
                                                model.Supported_Profile_ids.map((pid: string) => (
                                                    <span key={pid} className="inline-flex items-center rounded-md bg-purple-500/10 px-2 py-1 text-xs font-medium text-purple-400 ring-1 ring-inset ring-purple-500/20">
                                                        {pid}
                                                    </span>
                                                ))
                                            ) : (
                                                <p className="text-sm text-slate-500 italic">No specific profiles associated</p>
                                            )}
                                        </div>
                                    </div>

                                    {/* System Info */}
                                    <div className="border-t border-white/5 pt-4">
                                        <div className="grid grid-cols-2 gap-4 text-xs text-slate-500">
                                            <div>
                                                <span className="block mb-0.5">Tenant ID</span>
                                                <span className="text-slate-300 font-mono">{model.tenant_id}</span>
                                            </div>
                                            <div>
                                                <span className="block mb-0.5">Site ID</span>
                                                <span className="text-slate-300 font-mono">{model.site_id}</span>
                                            </div>
                                        </div>
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
