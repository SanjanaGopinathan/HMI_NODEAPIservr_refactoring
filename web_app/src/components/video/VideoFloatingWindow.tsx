import { useState, useRef, useEffect } from 'react';
import { X, Maximize, Minimize, ExternalLink } from 'lucide-react';
import type { Camera } from '../../lib/api';
import { cn } from '../../lib/utils';
import { API_URL } from '../../lib/api';

interface VideoFloatingWindowProps {
    camera: Camera;
    onClose: () => void;
}

export function VideoFloatingWindow({ camera, onClose }: VideoFloatingWindowProps) {
    const [isFullScreen, setIsFullScreen] = useState(false);
    const [isMinimized, setIsMinimized] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Construct Stream URL
    // We assume the backend is reachable via API_URL
    const streamUrl = `${API_URL}/stream/proxy?url=${encodeURIComponent(camera.rtsp_url)}&camera_id=${camera.id}`;

    const toggleFullScreen = () => {
        if (!document.fullscreenElement) {
            containerRef.current?.requestFullscreen();
            setIsFullScreen(true);
        } else {
            document.exitFullscreen();
            setIsFullScreen(false);
        }
    };

    // Handle ESC key to close fullscreen state update
    useEffect(() => {
        const handleChange = () => {
            setIsFullScreen(!!document.fullscreenElement);
        };
        document.addEventListener('fullscreenchange', handleChange);
        return () => document.removeEventListener('fullscreenchange', handleChange);
    }, []);

    if (isMinimized) {
        return (
            <div className="fixed bottom-4 right-4 z-50 flex items-center gap-3 rounded-lg border border-white/10 bg-slate-900 p-3 shadow-2xl animate-in slide-in-from-bottom">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-sm font-medium text-slate-200">{camera.name}</span>
                <button
                    onClick={() => setIsMinimized(false)}
                    className="ml-2 rounded p-1 hover:bg-white/10 text-slate-400 hover:text-white"
                >
                    <ExternalLink className="h-4 w-4" />
                </button>
                <button
                    onClick={onClose}
                    className="rounded p-1 hover:bg-white/10 text-slate-400 hover:text-white"
                >
                    <X className="h-4 w-4" />
                </button>
            </div>
        );
    }

    return (
        <div
            ref={containerRef}
            className={cn(
                "fixed z-50 overflow-hidden bg-black shadow-2xl transition-all duration-300 border border-white/10 flex flex-col",
                isFullScreen
                    ? "inset-0 rounded-none"
                    : "bottom-4 right-4 h-[360px] w-[640px] rounded-xl animate-in slide-in-from-bottom-10 fade-in"
            )}
        >
            {/* Header / Controls */}
            <div className={cn(
                "flex items-center justify-between bg-gradient-to-b from-black/80 to-transparent p-4 absolute top-0 left-0 right-0 z-10 transition-opacity",
                isFullScreen ? "opacity-0 hover:opacity-100" : "opacity-100"
            )}>
                <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                    <h3 className="text-sm font-medium text-white shadow-black drop-shadow-md">{camera.name}</h3>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setIsMinimized(true)}
                        className="rounded-lg bg-black/40 p-1.5 text-white/80 hover:bg-black/60 hover:text-white backdrop-blur-sm transition-colors"
                        title="Minimize"
                    >
                        <Minimize className="h-4 w-4" />
                    </button>
                    <button
                        onClick={toggleFullScreen}
                        className="rounded-lg bg-black/40 p-1.5 text-white/80 hover:bg-black/60 hover:text-white backdrop-blur-sm transition-colors"
                        title="Full Screen"
                    >
                        {isFullScreen ? <Minimize className="h-4 w-4" /> : <Maximize className="h-4 w-4" />}
                    </button>
                    <button
                        onClick={onClose}
                        className="rounded-lg bg-black/40 p-1.5 text-white/80 hover:bg-red-500/80 hover:text-white backdrop-blur-sm transition-colors"
                        title="Close"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Video Stream */}
            <div className="flex-1 bg-black relative flex items-center justify-center">
                {/* Loading / Placeholder */}
                <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                    <span className="animate-pulse">Connecting to stream...</span>
                </div>

                <img
                    src={streamUrl}
                    alt={camera.name}
                    className="h-full w-full object-contain relative z-0"
                    onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                        // Could show error state here
                    }}
                />
            </div>
        </div>
    );
}
