import { Fragment, useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { X, Plus, Trash2 } from 'lucide-react';
import { queries } from '../../lib/api';
import { useConfig } from '../settings/ConfigContext';
import { useQueryClient } from '@tanstack/react-query';

interface CreateProfileModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function CreateProfileModal({ isOpen, onClose }: CreateProfileModalProps) {
    const { tenant_id, site_id, gateway_id } = useConfig();
    const queryClient = useQueryClient();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        name: '',
        profile_id: '',
        targetInput: '',
        targets: [] as string[]
    });

    const addTarget = () => {
        if (!formData.targetInput.trim()) return;
        if (formData.targets.includes(formData.targetInput.trim())) return;

        setFormData(prev => ({
            ...prev,
            targets: [...prev.targets, prev.targetInput.trim()],
            targetInput: ''
        }));
    };

    const removeTarget = (target: string) => {
        setFormData(prev => ({
            ...prev,
            targets: prev.targets.filter(t => t !== target)
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        // Validation
        if (formData.targets.length === 0) {
            setError("At least one target class is required");
            setIsLoading(false);
            return;
        }

        try {
            // Generate ID if not provided, or use name-based
            const profileId = formData.profile_id || `PROFILE_${formData.name.toUpperCase().replace(/\s+/g, '_')}`;

            await queries.createProfile({
                profile_id: profileId,
                tenant_id,
                site_id,
                gateway_id,
                name: formData.name,
                targets: formData.targets
            });

            // Success
            queryClient.invalidateQueries({ queryKey: ['profiles'] });
            onClose();
            setFormData({
                name: '',
                profile_id: '',
                targetInput: '',
                targets: []
            });
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || 'Failed to create profile');
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTarget();
        }
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
                            <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-slate-900 border border-white/10 p-6 text-left align-middle shadow-xl transition-all">
                                <div className="flex items-center justify-between mb-4">
                                    <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-white">
                                        Create Detection Profile
                                    </Dialog.Title>
                                    <button
                                        onClick={onClose}
                                        className="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
                                    >
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    {error && (
                                        <div className="rounded-lg bg-rose-500/10 border border-rose-500/20 p-3 text-sm text-rose-400">
                                            {error}
                                        </div>
                                    )}

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">
                                            Profile Name
                                        </label>
                                        <input
                                            type="text"
                                            required
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                            placeholder="e.g. Person & Vehicle Detection"
                                        />
                                    </div>



                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">
                                            Detection Targets
                                        </label>
                                        <div className="flex gap-2 mb-2">
                                            <input
                                                type="text"
                                                value={formData.targetInput}
                                                onChange={(e) => setFormData({ ...formData, targetInput: e.target.value })}
                                                onKeyDown={handleKeyDown}
                                                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                                placeholder="Add target (e.g. person, car)"
                                            />
                                            <button
                                                type="button"
                                                onClick={addTarget}
                                                disabled={!formData.targetInput.trim()}
                                                className="rounded-lg bg-white/10 px-3 py-2 text-slate-300 hover:bg-white/20 transition-colors disabled:opacity-50"
                                            >
                                                <Plus className="h-4 w-4" />
                                            </button>
                                        </div>

                                        <div className="flex flex-wrap gap-2">
                                            {formData.targets.map((target) => (
                                                <span key={target} className="inline-flex items-center gap-1 rounded-md bg-cyan-500/10 px-2 py-1 text-xs font-medium text-cyan-400 ring-1 ring-inset ring-cyan-500/20">
                                                    {target}
                                                    <button
                                                        type="button"
                                                        onClick={() => removeTarget(target)}
                                                        className="ml-1 rounded-full p-0.5 hover:bg-cyan-500/20 text-cyan-400"
                                                    >
                                                        <X className="h-3 w-3" />
                                                    </button>
                                                </span>
                                            ))}
                                            {formData.targets.length === 0 && (
                                                <span className="text-sm text-slate-500 italic">No targets added yet</span>
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
                                            {isLoading ? 'Creating...' : 'Create Profile'}
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
