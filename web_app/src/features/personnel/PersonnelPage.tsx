import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Users, Plus, Search, Phone, Mail } from 'lucide-react';
import { queries } from '../../lib/api';
import { cn } from '../../lib/utils';

import { useConfig } from '../settings/ConfigContext';
import { CreatePersonnelModal } from './CreatePersonnelModal';

export function PersonnelPage() {
    const { tenant_id, site_id } = useConfig();
    const [filter, setFilter] = useState('');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

    const { data: personnel = [], isLoading, isError } = useQuery({
        queryKey: ['personnel', tenant_id, site_id],
        queryFn: () => queries.listPersonnel({ tenant_id, site_id }),
    });

    const filteredPersonnel = personnel.filter((person: any) =>
        person.name.toLowerCase().includes(filter.toLowerCase()) ||
        person.role.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Personnel</h1>
                    <p className="text-sm text-slate-400">Manage staff and on-call schedules.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Filter personnel..."
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
                        Add Personnel
                    </button>
                </div>
            </div>

            {isLoading ? (
                <div className="flex h-64 items-center justify-center text-slate-500">Loading personnel...</div>
            ) : isError ? (
                <div className="flex h-64 items-center justify-center text-rose-500">Failed to load personnel</div>
            ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {filteredPersonnel.map((person: any) => (
                        <div key={person._id} className="group relative flex flex-col rounded-xl border border-white/10 bg-slate-950/50 p-4 transition-all hover:bg-white/5">
                            <div className="mb-4 flex items-start justify-between">
                                <div className="rounded-lg bg-slate-800 p-2 text-slate-400 group-hover:bg-cyan-500/10 group-hover:text-cyan-400 transition-colors">
                                    <Users className="h-6 w-6" />
                                </div>
                                <div className={cn(
                                    "flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium border",
                                    person.on_call
                                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                        : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                                )}>
                                    <span className={cn("h-1.5 w-1.5 rounded-full", person.on_call ? "bg-amber-500" : "bg-slate-500")} />
                                    {person.on_call ? 'ON CALL' : 'OFF DUTY'}
                                </div>
                            </div>

                            <div className="mb-4 flex-1">
                                <h3 className="font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors truncate">{person.name}</h3>
                                <p className="text-sm text-slate-500 uppercase tracking-wider text-[10px] font-bold">{person.role}</p>

                                <div className="mt-3 space-y-2">
                                    {person.contact?.phone && (
                                        <div className="flex items-center gap-2 text-xs text-slate-400">
                                            <Phone className="h-3 w-3" />
                                            {person.contact.phone}
                                        </div>
                                    )}
                                    {person.contact?.email && (
                                        <div className="flex items-center gap-2 text-xs text-slate-400 truncate">
                                            <Mail className="h-3 w-3" />
                                            {person.contact.email}
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="flex items-center justify-between border-t border-white/5 pt-4">
                                <span className="text-xs text-slate-500 italic">Actions coming soon</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <CreatePersonnelModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
        </div>
    );
}
