import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Video, Brain, Shield, Users, Settings, Scan } from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Cameras', href: '/cameras', icon: Video },
    { name: 'Models', href: '/models', icon: Brain },
    { name: 'Profiles', href: '/profiles', icon: Scan },
    { name: 'Policies', href: '/policies', icon: Shield },
    { name: 'Personnel', href: '/personnel', icon: Users },
    { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
    const location = useLocation();

    return (
        <div className="flex h-screen w-64 flex-col gap-4 border-r border-white/10 bg-slate-950/80 p-4 backdrop-blur-xl">
            <div className="flex h-12 items-center px-2">
                <h1 className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-2xl font-bold tracking-tight text-transparent">
                    AI Orchestrator
                </h1>
            </div>
            <nav className="flex flex-col gap-2 mt-4">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            to={item.href}
                            className={cn(
                                "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition-all duration-200 group relative overflow-hidden",
                                isActive
                                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-[0_0_20px_-5px_rgba(6,182,212,0.3)]"
                                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent"
                            )}
                        >
                            {isActive && (
                                <div className="absolute inset-y-0 left-0 w-1 bg-cyan-500 rounded-r-full shadow-[0_0_10px_2px_rgba(6,182,212,0.6)]" />
                            )}
                            <item.icon className={cn("h-5 w-5 transition-colors", isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200")} />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>

            <div className="mt-auto">
                <div className="rounded-xl border border-white/5 bg-white/5 p-4 backdrop-blur-sm">
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 shadow-lg shadow-cyan-500/20" />
                        <div className="flex flex-col">
                            <span className="text-xs font-medium text-slate-200">System Admin</span>
                            <span className="text-[10px] text-slate-500">online</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
