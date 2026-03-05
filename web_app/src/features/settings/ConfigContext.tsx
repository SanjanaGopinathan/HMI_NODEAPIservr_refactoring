import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

// Define the shape of our configuration
interface ConfigState {
    tenant_id: string;
    site_id: string;
    gateway_id: string;
}

interface ConfigContextType extends ConfigState {
    updateConfig: (validConfig: Partial<ConfigState>) => void;
}

// Default values if nothing is in localStorage
const DEFAULT_CONFIG: ConfigState = {
    tenant_id: 'TENANT_01',
    site_id: 'SITE_01',
    gateway_id: 'GW_001',
};

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export function ConfigProvider({ children }: { children: ReactNode }) {
    // Initialize state from localStorage or defaults
    const [config, setConfig] = useState<ConfigState>(() => {
        const stored = localStorage.getItem('app_config');
        if (stored) {
            try {
                return { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
            } catch (e) {
                console.error("Failed to parse stored config", e);
            }
        }
        return DEFAULT_CONFIG;
    });

    // Save to localStorage whenever config changes
    useEffect(() => {
        localStorage.setItem('app_config', JSON.stringify(config));
    }, [config]);

    const updateConfig = (newConfig: Partial<ConfigState>) => {
        setConfig(prev => ({ ...prev, ...newConfig }));
    };

    return (
        <ConfigContext.Provider value={{ ...config, updateConfig }}>
            {children}
        </ConfigContext.Provider>
    );
}

// Custom hook for easy access
export function useConfig() {
    const context = useContext(ConfigContext);
    if (context === undefined) {
        throw new Error('useConfig must be used within a ConfigProvider');
    }
    return context;
}
