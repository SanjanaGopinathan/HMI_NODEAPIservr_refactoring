import { Fragment, useState } from 'react';
import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild } from '@headlessui/react';
import { X } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { queries, type CreateCameraParams } from '../../lib/api';

interface AddCameraModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export function AddCameraModal({ isOpen, onClose }: AddCameraModalProps) {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState<CreateCameraParams>({
        camera_id: '',
        name: '',
        rtsp_url: '',
        onvif_url: '',
        location: '',
        zone: '',
        userid: '',
        password: '',
    });

    const mutation = useMutation({
        mutationFn: queries.createCamera,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['cameras'] });
            onClose();
            setFormData({
                camera_id: '',
                name: '',
                rtsp_url: '',
                onvif_url: '',
                location: '',
                zone: '',
                userid: '',
                password: '',
            });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!formData.camera_id || !formData.name || !formData.rtsp_url) return;
        mutation.mutate(formData);
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
                            <DialogPanel className="w-full max-w-md transform overflow-hidden rounded-2xl border border-white/10 bg-slate-900 p-6 text-left align-middle shadow-xl transition-all">
                                <div className="flex items-center justify-between mb-4">
                                    <DialogTitle as="h3" className="text-lg font-medium leading-6 text-white">
                                        Add New Camera
                                    </DialogTitle>
                                    <button onClick={onClose} className="rounded-full p-1 text-slate-400 hover:bg-white/10 hover:text-white transition-colors">
                                        <X className="h-5 w-5" />
                                    </button>
                                </div>

                                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                                    <div>
                                        <label htmlFor="camera_id" className="block text-sm font-medium text-slate-300">Camera ID</label>
                                        <input
                                            type="text"
                                            id="camera_id"
                                            required
                                            placeholder="CAM_001"
                                            className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                            value={formData.camera_id}
                                            onChange={(e) => setFormData({ ...formData, camera_id: e.target.value })}
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="name" className="block text-sm font-medium text-slate-300">Name</label>
                                        <input
                                            type="text"
                                            id="name"
                                            required
                                            placeholder="Front Gate Camera"
                                            className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="location" className="block text-sm font-medium text-slate-300">Location</label>
                                        <input
                                            type="text"
                                            id="location"
                                            placeholder="Main Entrance"
                                            className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                            value={formData.location}
                                            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="rtsp_url" className="block text-sm font-medium text-slate-300">RTSP URL</label>
                                        <input
                                            type="text"
                                            id="rtsp_url"
                                            required
                                            placeholder="rtsp://admin:pass@192.168.1.100:554/stream"
                                            className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                            value={formData.rtsp_url}
                                            onChange={(e) => setFormData({ ...formData, rtsp_url: e.target.value })}
                                        />
                                    </div>

                                    <div>
                                        <label htmlFor="onvif_url" className="block text-sm font-medium text-slate-300">ONVIF URL (Optional)</label>
                                        <input
                                            type="text"
                                            id="onvif_url"
                                            placeholder="http://192.168.1.100:80/onvif/device_service"
                                            className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                            value={formData.onvif_url}
                                            onChange={(e) => setFormData({ ...formData, onvif_url: e.target.value })}
                                        />
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label htmlFor="userid" className="block text-sm font-medium text-slate-300">User ID (Optional)</label>
                                            <input
                                                type="text"
                                                id="userid"
                                                placeholder="admin"
                                                className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                                value={formData.userid || ''}
                                                onChange={(e) => setFormData({ ...formData, userid: e.target.value })}
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="password" className="block text-sm font-medium text-slate-300">Password (Optional)</label>
                                            <input
                                                type="password"
                                                id="password"
                                                placeholder="••••••"
                                                className="mt-1 block w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
                                                value={formData.password || ''}
                                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                            />
                                        </div>
                                    </div>

                                    <div className="mt-4 flex justify-end gap-3">
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
                                            className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            {mutation.isPending ? 'Creating...' : 'Create Camera'}
                                        </button>
                                    </div>
                                    {mutation.isError && (
                                        <p className="text-sm text-rose-500 mt-2">Error creating camera: {mutation.error.message}</p>
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
