import { Fragment, useState, } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, Shield } from 'lucide-react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { queries } from '../../lib/api';
import { useConfig } from '../settings/ConfigContext';

interface CreatePolicyModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const SEVERITY_LEVELS = ['INFO', 'WARNING', 'CRITICAL'];
const CHANNELS = ['PTT', 'SMS', 'Email'];

export function CreatePolicyModal({ isOpen, onClose }: CreatePolicyModalProps) {
    const { tenant_id, site_id } = useConfig();
    const queryClient = useQueryClient();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { data: personnel = [] } = useQuery({
        queryKey: ['personnel', tenant_id, site_id],
        queryFn: () => queries.listPersonnel({ tenant_id, site_id }),
        enabled: isOpen,
    });

    const [formData, setFormData] = useState({
        policy_id: '',
        anomaly_type: 'Person_Detection',
        min_severity: 'WARNING',
        channels: [] as string[],
        person_ids: [] as string[],
        enabled: true
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            // Auto-generate ID if empty with random suffix to ensure uniqueness
            const randomSuffix = Math.floor(Math.random() * 10000).toString().padStart(4, '0');
            const policyId = formData.policy_id || `POLICY_${formData.anomaly_type.toUpperCase()}_${randomSuffix}`;

            // Filter severity levels based on min_severity
            const minSeverityIndex = SEVERITY_LEVELS.indexOf(formData.min_severity);
            const applicableSeverities = SEVERITY_LEVELS.slice(minSeverityIndex);

            await queries.createPolicy({
                policy_id: policyId,
                tenant_id,
                site_id,
                anomaly_type: formData.anomaly_type,
                severity_levels: applicableSeverities,
                channels: formData.channels,
                person_ids: formData.person_ids,
                min_severity: formData.min_severity,
                enabled: formData.enabled
            });

            // Success
            queryClient.invalidateQueries({ queryKey: ['policies'] });
            onClose();
            setFormData({
                policy_id: '',
                anomaly_type: 'Person_Detection',
                min_severity: 'WARNING',
                channels: [],
                person_ids: [],
                enabled: true
            });
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || 'Failed to create policy');
        } finally {
            setIsLoading(false);
        }
    };

    const toggleChannel = (channel: string) => {
        setFormData(prev => ({
            ...prev,
            channels: prev.channels.includes(channel)
                ? prev.channels.filter(c => c !== channel)
                : [...prev.channels, channel]
        }));
    };

    const togglePerson = (personId: string) => {
        setFormData(prev => ({
            ...prev,
            person_ids: prev.person_ids.includes(personId)
                ? prev.person_ids.filter(id => id !== personId)
                : [...prev.person_ids, personId]
        }));
    };

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
                                <div className="flex items-center justify-between mb-4">
                                    <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-white flex items-center gap-2">
                                        <Shield className="h-5 w-5 text-cyan-400" />
                                        Create Alert Policy
                                    </Dialog.Title>
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <form onSubmit={handleSubmit} className="space-y-5">
                                    {error && (
                                        <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-sm text-rose-400">
                                            {error}
                                        </div>
                                    )}

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-400 mb-1">
                                                Anomaly Type
                                            </label>
                                            <input
                                                type="text"
                                                value={formData.anomaly_type}
                                                onChange={(e) => setFormData({ ...formData, anomaly_type: e.target.value })}
                                                className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                                placeholder="e.g. Unauth_Access"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-400 mb-1">
                                                Min Severity
                                            </label>
                                            <select
                                                value={formData.min_severity}
                                                onChange={(e) => setFormData({ ...formData, min_severity: e.target.value })}
                                                className="w-full rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-slate-200 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                            >
                                                {SEVERITY_LEVELS.map(level => (
                                                    <option key={level} value={level}>{level}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">
                                            Notification Channels
                                        </label>
                                        <div className="flex flex-wrap gap-2">
                                            {CHANNELS.map(channel => (
                                                <button
                                                    key={channel}
                                                    type="button"
                                                    onClick={() => toggleChannel(channel)}
                                                    className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-all ${formData.channels.includes(channel)
                                                        ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50'
                                                        : 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10'
                                                        }`}
                                                >
                                                    {channel}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">
                                            Notify Personnel
                                        </label>
                                        <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                                            {personnel.length === 0 ? (
                                                <p className="text-xs text-slate-500 italic">No personnel found.</p>
                                            ) : (
                                                personnel.map((person: any) => (
                                                    <div
                                                        key={person._id}
                                                        onClick={() => togglePerson(person._id)}
                                                        className={`flex items-center justify-between p-2 rounded-lg border cursor-pointer transition-all ${formData.person_ids.includes(person._id)
                                                            ? 'bg-cyan-500/10 border-cyan-500/30'
                                                            : 'bg-white/5 border-white/5 hover:bg-white/10'
                                                            }`}
                                                    >
                                                        <div>
                                                            <div className="text-sm text-slate-200">{person.name}</div>
                                                            <div className="text-xs text-slate-500">{person.role}</div>
                                                        </div>
                                                        <div className={`h-4 w-4 rounded-full border ${formData.person_ids.includes(person._id)
                                                            ? 'bg-cyan-500 border-cyan-500'
                                                            : 'border-slate-600'
                                                            }`} />
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </div>

                                    <div className="mt-6 flex justify-end gap-3 pt-4 border-t border-white/5">
                                        <button
                                            type="button"
                                            onClick={onClose}
                                            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={isLoading}
                                            className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {isLoading ? 'Creating...' : 'Create Policy'}
                                        </button>
                                    </div>
                                </form>
                            </Dialog.Panel>
                        </Transition.Child>
                    </div>
                </div>
            </Dialog>
        </Transition>
    );
}
