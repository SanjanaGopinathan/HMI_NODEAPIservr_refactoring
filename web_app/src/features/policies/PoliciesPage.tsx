import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Shield, Plus, Search, Users } from 'lucide-react';
import { queries } from '../../lib/api';
import { cn } from '../../lib/utils';

import { useConfig } from '../settings/ConfigContext';
import { CreatePolicyModal } from './CreatePolicyModal';
import { EditPolicyModal } from './EditPolicyModal';
import { ViewPolicySubscribersModal } from './ViewPolicySubscribersModal';

export function PoliciesPage() {
    const { tenant_id, site_id } = useConfig();
    const [filter, setFilter] = useState('');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [selectedPolicy, setSelectedPolicy] = useState<any>(null);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [isViewSubscribersModalOpen, setIsViewSubscribersModalOpen] = useState(false);

    const { data: policies = [], isLoading, isError } = useQuery({
        queryKey: ['policies', tenant_id, site_id],
        queryFn: () => queries.listPolicies({ tenant_id, site_id }),
    });

    const filteredPolicies = policies.filter((policy: any) =>
        policy._id.toLowerCase().includes(filter.toLowerCase()) ||
        policy.anomaly_type.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">Alert Policies</h1>
                    <p className="text-sm text-slate-400">Configure alert rules and notification channels.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Filter policies..."
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
                        Create Policy
                    </button>
                </div>
            </div>

            {isLoading ? (
                <div className="flex h-64 items-center justify-center text-slate-500">Loading policies...</div>
            ) : isError ? (
                <div className="flex h-64 items-center justify-center text-rose-500">Failed to load policies</div>
            ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {filteredPolicies.map((policy: any) => (
                        <div key={policy._id} className="group relative flex flex-col rounded-xl border border-white/10 bg-slate-950/50 p-4 transition-all hover:bg-white/5">
                            <div className="mb-4 flex items-start justify-between">
                                <div className="rounded-lg bg-slate-800 p-2 text-slate-400 group-hover:bg-cyan-500/10 group-hover:text-cyan-400 transition-colors">
                                    <Shield className="h-6 w-6" />
                                </div>
                                <div className={cn(
                                    "flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium border",
                                    policy.enabled
                                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                        : "bg-slate-500/10 text-slate-400 border-slate-500/20"
                                )}>
                                    <span className={cn("h-1.5 w-1.5 rounded-full", policy.enabled ? "bg-emerald-500" : "bg-slate-500")} />
                                    {policy.enabled ? 'ENABLED' : 'DISABLED'}
                                </div>
                            </div>

                            <div className="mb-4 flex-1">
                                <h3 className="font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors truncate" title={policy._id}>
                                    {policy.anomaly_type.replace(/_/g, ' ')}
                                </h3>
                                <p className="text-sm text-slate-500 truncate">Min Severity: <span className="text-slate-300">{policy.min_severity}</span></p>

                                <div className="mt-3 space-y-2">
                                    {policy.routes?.slice(0, 2).map((route: any, i: number) => (
                                        <div key={i} className="flex items-center justify-between text-xs bg-white/5 rounded px-2 py-1">
                                            <span className="text-slate-400">{route.severity}</span>
                                            <div className="flex gap-1">
                                                {route.channels?.map((ch: string) => (
                                                    <span key={ch} className="text-[10px] text-cyan-400 bg-cyan-500/10 px-1 rounded">{ch}</span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="flex items-center justify-between border-t border-white/5 pt-4">
                                <div className="flex gap-2">
                                    <div
                                        onClick={() => {
                                            setSelectedPolicy(policy);
                                            setIsViewSubscribersModalOpen(true);
                                        }}
                                        className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors cursor-pointer"
                                        title="View Subscribers"
                                    >
                                        <Users className="h-4 w-4" />
                                    </div>
                                </div>
                                <button
                                    onClick={() => {
                                        setSelectedPolicy(policy);
                                        setIsEditModalOpen(true);
                                    }}
                                    className="text-xs font-medium text-cyan-500 hover:text-cyan-400 transition-colors"
                                >
                                    Edit
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <CreatePolicyModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
            <EditPolicyModal
                isOpen={isEditModalOpen}
                onClose={() => {
                    setIsEditModalOpen(false);
                    setSelectedPolicy(null);
                }}
                policy={selectedPolicy}
            />
            <ViewPolicySubscribersModal
                isOpen={isViewSubscribersModalOpen}
                onClose={() => {
                    setIsViewSubscribersModalOpen(false);
                    setSelectedPolicy(null);
                }}
                policy={selectedPolicy}
            />
        </div>
    );
}
