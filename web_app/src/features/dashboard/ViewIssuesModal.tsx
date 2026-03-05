import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, AlertTriangle, AlertCircle } from 'lucide-react';

interface ViewIssuesModalProps {
    isOpen: boolean;
    onClose: () => void;
    issues: string[];
}

export function ViewIssuesModal({ isOpen, onClose, issues }: ViewIssuesModalProps) {
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
                            <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-slate-900 border border-rose-500/20 p-6 text-left align-middle shadow-xl transition-all relative">
                                <div className="absolute top-0 right-0 p-4">
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="rounded-full bg-rose-500/10 p-3 text-rose-500">
                                        <AlertTriangle className="h-6 w-6" />
                                    </div>
                                    <div>
                                        <Dialog.Title as="h3" className="text-lg font-bold leading-6 text-white">
                                            System Issues
                                        </Dialog.Title>
                                        <p className="text-sm text-slate-400">
                                            The following items require your attention.
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                    {Array.isArray(issues) && issues.length > 0 ? (
                                        issues.map((issue, index) => (
                                            <div key={index} className="flex gap-3 rounded-lg border border-rose-500/20 bg-rose-500/5 p-3">
                                                <AlertCircle className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
                                                <p className="text-sm text-slate-200">{typeof issue === 'string' ? issue : JSON.stringify(issue)}</p>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-center py-8 text-slate-500 italic">
                                            No critical issues found. System is healthy.
                                        </div>
                                    )}
                                </div>

                                <div className="mt-6 flex justify-end">
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-white hover:bg-white/20 transition-colors"
                                    >
                                        Close
                                    </button>
                                </div>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
