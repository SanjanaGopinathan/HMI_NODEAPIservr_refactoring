import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Brain, Plus, Search, Layers } from 'lucide-react';
import { queries } from '../../lib/api';
import { cn } from '../../lib/utils';

import { useConfig } from '../settings/ConfigContext';
import { CreateModelModal } from './CreateModelModal';
import { ModelDetailsModal } from './ModelDetailsModal';
import { DeployModelModal } from './DeployModelModal';

export function ModelsPage() {
    const { tenant_id, site_id } = useConfig();
    const [filter, setFilter] = useState('');
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [selectedModel, setSelectedModel] = useState<any>(null);
    const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
    const [isDeployModalOpen, setIsDeployModalOpen] = useState(false);

    const { data: models = [], isLoading, isError } = useQuery({
        queryKey: ['models', tenant_id, site_id],
        queryFn: () => queries.listModels({ tenant_id, site_id }),
    });

    const filteredModels = models.filter((model: any) =>
        model.name.toLowerCase().includes(filter.toLowerCase()) ||
        model.framework_id.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-2xl font-bold tracking-tight text-white">AI Models</h1>
                    <p className="text-sm text-slate-400">Manage computer vision models and deployment.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Filter models..."
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
                        Add Model
                    </button>
                </div>
            </div>

            {isLoading ? (
                <div className="flex h-64 items-center justify-center text-slate-500">Loading models...</div>
            ) : isError ? (
                <div className="flex h-64 items-center justify-center text-rose-500">Failed to load models</div>
            ) : (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {filteredModels.map((model: any) => (
                        <div key={model._id} className="group relative flex flex-col rounded-xl border border-white/10 bg-slate-950/50 p-4 transition-all hover:bg-white/5">
                            <div className="mb-4 flex items-start justify-between">
                                <div className="rounded-lg bg-slate-800 p-2 text-slate-400 group-hover:bg-cyan-500/10 group-hover:text-cyan-400 transition-colors">
                                    <Brain className="h-6 w-6" />
                                </div>
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

                            <div className="mb-4 flex-1">
                                <h3 className="font-semibold text-slate-100 group-hover:text-cyan-400 transition-colors truncate">{model.name}</h3>
                                <p className="text-sm text-slate-500 truncate">{model.framework_id}</p>
                                <div className="mt-2 flex gap-2">
                                    {model.Supported_Profile_ids?.slice(0, 2).map((pid: string) => (
                                        <span key={pid} className="inline-flex items-center rounded-md bg-white/5 px-2 py-1 text-xs font-medium text-slate-400 ring-1 ring-inset ring-white/10">
                                            {pid.split('_').pop()}
                                        </span>
                                    ))}
                                    {model.Supported_Profile_ids?.length > 2 && (
                                        <span className="inline-flex items-center rounded-md bg-white/5 px-2 py-1 text-xs font-medium text-slate-400 ring-1 ring-inset ring-white/10">
                                            +{model.Supported_Profile_ids.length - 2}
                                        </span>
                                    )}
                                </div>
                            </div>

                            <div className="flex items-center justify-between border-t border-white/5 pt-4">
                                <div className="flex gap-2">
                                    <div
                                        onClick={() => {
                                            setSelectedModel(model);
                                            setIsDetailsModalOpen(true);
                                        }}
                                        className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-slate-400 hover:text-cyan-400 hover:bg-cyan-500/10 transition-colors cursor-pointer"
                                        title="View Details"
                                    >
                                        <Layers className="h-4 w-4" />
                                    </div>
                                </div>
                                <button
                                    onClick={() => {
                                        setSelectedModel(model);
                                        setIsDeployModalOpen(true);
                                    }}
                                    className="text-xs font-medium text-cyan-500 hover:text-cyan-400 transition-colors"
                                >
                                    Deploy
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <CreateModelModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
            <ModelDetailsModal
                isOpen={isDetailsModalOpen}
                onClose={() => {
                    setIsDetailsModalOpen(false);
                    setSelectedModel(null);
                }}
                model={selectedModel}
            />
            <DeployModelModal
                isOpen={isDeployModalOpen}
                onClose={() => {
                    setIsDeployModalOpen(false);
                    setSelectedModel(null);
                }}
                model={selectedModel}
            />
        </div>
    );
}
