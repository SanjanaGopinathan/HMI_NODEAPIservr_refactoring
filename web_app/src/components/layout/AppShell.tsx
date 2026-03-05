import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface AppShellProps {
    children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
    return (
        <div className="flex h-screen w-full bg-slate-950 text-slate-50 overflow-hidden font-sans">
            <Sidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
                {localStorage.getItem('DEMO_MODE') === 'true' && (
                    <div className="bg-indigo-600 px-4 py-1 text-center text-xs font-bold text-white shadow-lg z-50">
                        DEMO MODE ACTIVE - Data is simulated and will reset on reload.
                    </div>
                )}
                <Header />
                <main className="flex-1 overflow-auto p-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                    {children}
                </main>
            </div>
        </div>
    );
}
