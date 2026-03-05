import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, Users, Phone, Mail } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { queries } from '../../lib/api';
import { useConfig } from '../settings/ConfigContext';
import { cn } from '../../lib/utils';

interface ViewPolicySubscribersModalProps {
    isOpen: boolean;
    onClose: () => void;
    policy: any;
}

export function ViewPolicySubscribersModal({ isOpen, onClose, policy }: ViewPolicySubscribersModalProps) {
    const { tenant_id, site_id } = useConfig();

    const { data: personnel = [], isLoading } = useQuery({
        queryKey: ['personnel', tenant_id, site_id],
        queryFn: () => queries.listPersonnel({ tenant_id, site_id }),
        enabled: isOpen,
    });

    if (!policy) return null;

    // Determine subscribed personnel
    // Assuming policy.person_ids contains the IDs, or we extract from routes
    const subscribedPersonIds = new Set<string>();

    if (policy.person_ids && Array.isArray(policy.person_ids)) {
        policy.person_ids.forEach((id: string) => subscribedPersonIds.add(id));
    }

    if (policy.routes && Array.isArray(policy.routes)) {
        policy.routes.forEach((route: any) => {
            if (route.targets && Array.isArray(route.targets)) {
                route.targets.forEach((target: any) => {
                    if (target.target_type === 'PERSON' && target.value) {
                        subscribedPersonIds.add(target.value);
                    }
                });
            }
        });
    }

    const subscribedPersonnel = personnel.filter((p: any) =>
        subscribedPersonIds.has(p._id) || subscribedPersonIds.has(p.person_id)
    );

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
                            <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-slate-900 border border-white/10 p-6 text-left align-middle shadow-xl transition-all">
                                <div className="flex items-center justify-between mb-4">
                                    <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-white flex items-center gap-2">
                                        <Users className="h-5 w-5 text-cyan-400" />
                                        Subscribed Personnel
                                    </Dialog.Title>
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <div className="mb-4">
                                    <h4 className="text-sm font-medium text-slate-300 mb-1">Policy: <span className="text-cyan-400">{policy.anomaly_type?.replace(/_/g, ' ')}</span></h4>
                                    <p className="text-xs text-slate-500">
                                        The following personnel are notified when this policy is triggered.
                                    </p>
                                </div>

                                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                                    {isLoading ? (
                                        <div className="text-center py-8 text-slate-500">Loading personnel...</div>
                                    ) : subscribedPersonnel.length === 0 ? (
                                        <div className="text-center py-8 text-slate-500 border border-dashed border-white/10 rounded-lg">
                                            No subscribers found.
                                        </div>
                                    ) : (
                                        subscribedPersonnel.map((person: any) => (
                                            <div key={person._id} className="group flex flex-col rounded-lg border border-white/5 bg-white/5 p-3 hover:bg-white/10 transition-colors">
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-3">
                                                        <div className={cn(
                                                            "h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold",
                                                            person.on_call ? "bg-amber-500/10 text-amber-500" : "bg-slate-700 text-slate-300"
                                                        )}>
                                                            {person.name.substring(0, 2).toUpperCase()}
                                                        </div>
                                                        <div>
                                                            <div className="text-sm font-medium text-slate-200">{person.name}</div>
                                                            <div className="text-xs text-slate-500">{person.role}</div>
                                                        </div>
                                                    </div>
                                                    {person.on_call && (
                                                        <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20">
                                                            ON CALL
                                                        </span>
                                                    )}
                                                </div>

                                                <div className="grid grid-cols-2 gap-2 mt-1">
                                                    {person.contact?.phone && (
                                                        <div className="flex items-center gap-1.5 text-xs text-slate-400 overflow-hidden">
                                                            <Phone className="h-3 w-3 flex-shrink-0" />
                                                            <span className="truncate">{person.contact.phone}</span>
                                                        </div>
                                                    )}
                                                    {person.contact?.email && (
                                                        <div className="flex items-center gap-1.5 text-xs text-slate-400 overflow-hidden">
                                                            <Mail className="h-3 w-3 flex-shrink-0" />
                                                            <span className="truncate">{person.contact.email}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>

                                <div className="mt-6 flex justify-end pt-4 border-t border-white/5">
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg bg-white/5 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/10 hover:text-white transition-colors"
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
