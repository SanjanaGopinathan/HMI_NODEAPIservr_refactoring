import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Scan, Plus, Search, Target } from 'lucide-react';
import { queries } from '../../lib/api';
import { cn } from '../../lib/utils';
import { useConfig } from '../settings/ConfigContext';
import { CreateProfileModal } from './CreateProfileModal';
import { EditProfileModal } from './EditProfileModal';

export function ProfilesPage() {
    const { tenant_id, site_id } = useConfig();
    const [filter, setFilter] = useState('');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [selectedProfile, setSelectedProfile] = useState<any>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);

    const { data: profiles = [], isLoading, isError } = useQuery({
        queryKey: ['profiles', tenant_id, site_id],
        queryFn: () => queries.listProfiles({ tenant_id, site_id }),
    });

    const filteredProfiles = profiles.filter((profile: any) =>
        profile.name.toLowerCase().includes(filter.toLowerCase()) ||
        (profile.targets || []).some((t: string) => t.toLowerCase().includes(filter.toLowerCase()))
    );

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Detection Profiles</h1>
                    <p className="text-sm text-slate-400">Manage object detection profiles and target classes.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Filter profiles..."
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="h-9 w-64 rounded-lg border border-white/10 bg-white/5 pl-9 pr-4 text-sm text-slate-200 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition-all"
                        />
                    </div>
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 transition-colors shadow-lg shadow-cyan-500/20"
                    >
                        <Plus className="h-4 w-4" />
                        Create Profile
                    </button>
                </div>
            </div>

            {isLoading ? (
                <div className="flex h-64 items-center justify-center text-slate-500">Loading profiles...</div>
            ) : isError ? (
                <div className="flex h-64 items-center justify-center text-rose-500">Failed to load profiles</div>
            ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {filteredProfiles.length > 0 ? (
                        filteredProfiles.map((profile: any) => (
                            <div key={profile._id} className="group relative flex flex-col rounded-xl border border-white/10 bg-slate-950/50 p-4 transition-all hover:bg-white/5">
                                <div className="mb-4 flex items-start justify-between">
                                    <div className="rounded-lg bg-slate-800 p-2 text-slate-400 group-hover:bg-cyan-500/10 group-hover:text-cyan-400 transition-colors">
                                        <Scan className="h-6 w-6" />
                                    </div>
                                    <div className="flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium border bg-slate-500/10 text-slate-400 border-slate-500/20">
                                        v{profile.version || '1.0'}
                                    </div>
                                </div>

                                <div className="mb-4 flex-1">
                                    <h3 className="font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors truncate" title={profile.name}>
                                        {profile.name}
                                    </h3>

                                    <div className="mt-3">
                                        <p className="text-xs text-slate-500 mb-2">Detection Targets:</p>
                                        <div className="flex flex-wrap gap-1.5">
                                            {profile.targets?.map((target: string, i: number) => (
                                                <span key={i} className="inline-flex items-center rounded bg-white/5 px-2 py-1 text-xs font-medium text-cyan-200 ring-1 ring-inset ring-white/10">
                                                    <Target className="mr-1 h-3 w-3 opacity-50" />
                                                    {target}
                                                </span>
                                            ))}
                                            {(!profile.targets || profile.targets.length === 0) && (
                                                <span className="text-xs text-slate-600 italic">No targets defined</span>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-end border-t border-white/5 pt-4">
                                    <button
                                        onClick={() => {
                                            setSelectedProfile(profile);
                                            setIsEditModalOpen(true);
                                        }}
                                        className="text-xs font-medium text-cyan-500 hover:text-cyan-400 transition-colors"
                                    >
                                        Edit
                                    </button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="col-span-full py-12 text-center text-slate-500">
                            No profiles found.
                        </div>
                    )}
                </div>
            )}

            <CreateProfileModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
            <EditProfileModal
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setSelectedProfile(null);
                }}
                profile={selectedProfile}
            />
        </div>
    );
}
