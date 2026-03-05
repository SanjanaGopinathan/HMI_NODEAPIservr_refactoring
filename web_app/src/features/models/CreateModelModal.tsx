import { Fragment, useState } from 'react';
import { Dialog, Transition, Listbox } from '@headlessui/react';
import { X, Check, ChevronDown } from 'lucide-react';
import { queries } from '../../lib/api';
import { useConfig } from '../settings/ConfigContext';
import { useQueryClient, useQuery } from '@tanstack/react-query';
import { cn } from '../../lib/utils';

interface CreateModelModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function CreateModelModal({ isOpen, onClose }: CreateModelModalProps) {
    const { tenant_id, site_id, gateway_id } = useConfig();
    const queryClient = useQueryClient();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { data: profiles = [] } = useQuery({
        queryKey: ['profiles', tenant_id, site_id],
        queryFn: () => queries.listProfiles({ tenant_id, site_id }),
    });

    const [formData, setFormData] = useState({
        name: '',
        framework_id: 'openvino-2024.1',
        model_id: '',
        supported_profile_ids: [] as string[]
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            // Generate ID if not provided, or use name-based
            const modelId = formData.model_id || `MODEL_${formData.name.toUpperCase().replace(/\s+/g, '_')}`;

            await queries.createModel({
                model_id: modelId,
                tenant_id,
                site_id,
                gateway_id,
                name: formData.name,
                framework_id: formData.framework_id,
                supported_profile_ids: formData.supported_profile_ids,
                status: 'ACTIVE'
            });

            // Success
            queryClient.invalidateQueries({ queryKey: ['models'] });
            onClose();
            setFormData({
                name: '',
                framework_id: 'openvino-2024.1',
                model_id: '',
                supported_profile_ids: []
            });
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || 'Failed to create model');
        } finally {
            setIsLoading(false);
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
                                        Add New Model
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
                                            Model Name
                                        </label>
                                        <input
                                            type="text"
                                            required
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                            placeholder="e.g. PPE Violation Detector"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">
                                            Framework ID
                                        </label>
                                        <select
                                            value={formData.framework_id}
                                            onChange={(e) => setFormData({ ...formData, framework_id: e.target.value })}
                                            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50"
                                        >
                                            <option value="openvino-2024.1" className="bg-slate-900">OpenVINO 2024.1</option>
                                            <option value="tensorflow-2.15" className="bg-slate-900">TensorFlow 2.15</option>
                                            <option value="pytorch-2.2" className="bg-slate-900">PyTorch 2.2</option>
                                            <option value="onnx-1.15" className="bg-slate-900">ONNX 1.15</option>
                                        </select>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-1">
                                            Supported Profiles
                                        </label>
                                        <Listbox
                                            value={formData.supported_profile_ids}
                                            onChange={(value) => setFormData({ ...formData, supported_profile_ids: value })}
                                            multiple
                                        >
                                            <div className="relative mt-1">
                                                <Listbox.Button className="relative w-full cursor-default rounded-lg border border-white/10 bg-white/5 py-2 pl-3 pr-10 text-left text-sm text-slate-200 focus:outline-none focus-visible:border-cyan-500/50 focus-visible:ring-1 focus-visible:ring-cyan-500/50">
                                                    <span className="block truncate">
                                                        {formData.supported_profile_ids.length === 0
                                                            ? 'Select profiles...'
                                                            : `${formData.supported_profile_ids.length} profiles selected`}
                                                    </span>
                                                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                        <ChevronDown
                                                            className="h-5 w-5 text-slate-400"
                                                            aria-hidden="true"
                                                        />
                                                    </span>
                                                </Listbox.Button>
                                                <Transition
                                                    as={Fragment}
                                                    leave="transition ease-in duration-100"
                                                    leaveFrom="opacity-100"
                                                    leaveTo="opacity-0"
                                                >
                                                    <Listbox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-slate-900 py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm border border-white/10 z-50">
                                                        {profiles.length === 0 ? (
                                                            <div className="relative cursor-default select-none py-2 pl-4 pr-4 text-slate-500 italic">
                                                                No profiles found.
                                                            </div>
                                                        ) : (
                                                            profiles.map((profile: any) => (
                                                                <Listbox.Option
                                                                    key={profile.profile_id || profile._id}
                                                                    className={({ active }) =>
                                                                        `relative cursor-default select-none py-2 pl-10 pr-4 ${active ? 'bg-cyan-900/30 text-cyan-200' : 'text-slate-300'
                                                                        }`
                                                                    }
                                                                    value={profile.profile_id || profile._id}
                                                                >
                                                                    {({ selected }) => (
                                                                        <>
                                                                            <span
                                                                                className={`block truncate ${selected ? 'font-medium' : 'font-normal'
                                                                                    }`}
                                                                            >
                                                                                {profile.name}
                                                                            </span>
                                                                            {selected ? (
                                                                                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-cyan-400">
                                                                                    <Check className="h-4 w-4" aria-hidden="true" />
                                                                                </span>
                                                                            ) : null}
                                                                        </>
                                                                    )}
                                                                </Listbox.Option>
                                                            ))
                                                        )}
                                                    </Listbox.Options>
                                                </Transition>
                                            </div>
                                        </Listbox>
                                        <p className="mt-1 text-xs text-slate-500">
                                            Select one or more profiles this model supports.
                                        </p>
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
                                            {isLoading ? 'Creating...' : 'Create Model'}
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
