import axios from 'axios';

// Orchestrator API (Workflows, Queries)
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8020';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

// --- Types ---

// --- Types ---

export interface CreateCameraParams {
    camera_id: string;
    tenant_id?: string;
    site_id?: string;
    gateway_id?: string;
    name: string;
    rtsp_url: string;
    onvif_url: string;
    location?: string;
    zone?: string;
    userid?: string;
    password?: string;
}

export interface SiteHealth {
    health_score: number;
    cameras_active: number;
    cameras_inactive: number;
    cameras_without_model: string[];
    cameras_without_policy: string[];
    cameras_without_profiles: string[];
    recommendations: string[];
    issues: string[];
}

export interface CameraRequest {
    tenant_id?: string;
    site_id?: string;
    gateway_id?: string;
    location?: string;
    status?: string;
}

export interface Camera {
    id: string;
    name: string;
    rtsp_url: string;
    location: string;
    status: string;
    // Add other fields as needed from MCP response
}

export interface StickyDefaults {
    effective_defaults: {
        tenant_id: string | null;
        site_id: string | null;
        gateway_id: string | null;
    };
    last_used: {
        tenant_id: string | null;
        site_id: string | null;
        gateway_id: string | null;
    };
}

// --- API Functions ---

export interface ConfigureMapperRequest {
    gateway_id: string;
}

export const realQueries = {
    setupPPESite: async (data: any) => {
        const response = await api.post('/workflows/setup_ppe_site', data);
        return response.data;
    },

    enablePPE: async (camera_id: string, params?: { tenant_id?: string; site_id?: string; gateway_id?: string }) => {
        const response = await api.post('/workflows/configure_ppe', {
            camera_id,
            ...params
        });
        return response.data;
    },

    disablePPE: async (camera_id: string, params?: { tenant_id?: string; site_id?: string; gateway_id?: string }) => {
        const response = await api.post('/workflows/disable_ppe', {
            camera_id,
            ...params
        });
        return response.data;
    },

    createCamera: async (params: CreateCameraParams) => {
        const response = await api.post('/workflows/create_camera', params);
        return response.data;
    },

    getSiteHealth: async (params: { tenant_id?: string; site_id?: string; gateway_id?: string }) => {
        const response = await api.post<SiteHealth>('/query/site-health', params);
        return response.data;
    },

    getStickyDefaults: async () => {
        const response = await api.get<StickyDefaults>('/query/sticky-defaults');
        return response.data;
    },

    listCameras: async (params: CameraRequest) => {
        console.log('listCameras request params:', params, 'time:', new Date().toISOString());
        const response = await api.post<{ cameras: any[] }>('/query/cameras', params);
        console.log('listCameras response:', response.data);
        const list = Array.isArray(response.data.cameras) ? response.data.cameras : [];
        console.log('Fetched listCameras request params:', params, 'time:', new Date().toISOString());
        return list.map((cam: any) => ({
            ...cam,
            id: cam.id || cam._id, // Ensure id exists by mapping _id if needed
            rtsp_url: cam.rtsp_url ||
                cam.asset_info?.rtsp_url ||
                cam.asset_info?.camera?.stream?.rtsp_url ||
                '' // Map nested RTSP URL (schema: asset_info.camera.stream.rtsp_url)
        })) as Camera[];

    },

    listGateways: async (params: { tenant_id?: string; site_id?: string }) => {
        const response = await api.post<{ gateways: any[] }>('/query/gateways', params);
        console.log('listGateways response:', response.data);
        return Array.isArray(response.data.gateways) ? response.data.gateways : [];
    },

    listModels: async (params: { tenant_id?: string; site_id?: string }) => {
        const response = await api.post<{ models: any[] }>('/query/models', params);
        console.log('listModels response:', response.data);
        return Array.isArray(response.data.models) ? response.data.models : [];
    },

    createModel: async (params: {
        model_id: string;
        tenant_id?: string;
        site_id?: string;
        gateway_id?: string;
        name: string;
        framework_id: string;
        supported_profile_ids?: string[];
        status?: string;
    }) => {
        const response = await api.post('/workflows/create_model', params);
        return response.data;
    },

    listPolicies: async (params: { tenant_id?: string; site_id?: string }) => {
        const response = await api.post<{ policies: any[] }>('/query/policies', params);
        console.log('listPolicies response:', response.data);
        return Array.isArray(response.data.policies) ? response.data.policies : [];
    },

    createPolicy: async (params: {
        policy_id: string;
        tenant_id?: string;
        site_id?: string;
        anomaly_type: string;
        severity_levels: string[];
        channels: string[];
        person_ids: string[];
        min_severity?: string;
        enabled?: boolean;
        priority?: number;
    }) => {
        const response = await api.post('/workflows/create_policy', params);
        return response.data;
    },

    updatePolicy: async (params: {
        policy_id: string;
        tenant_id?: string;
        site_id?: string;
        anomaly_type?: string;
        severity_levels?: string[];
        channels?: string[];
        person_ids?: string[];
        min_severity?: string;
        enabled?: boolean;
        priority?: number;
    }) => {
        // Assuming there is an endpoint for update, if not we might need to use create with overwrite or a specific update endpoint.
        // For now using /workflows/update_policy assuming it exists or will be created.
        const response = await api.post('/workflows/update_policy', params);
        return response.data;
    },

    listPersonnel: async (params: { tenant_id?: string; site_id?: string }) => {
        const response = await api.post<{ personnel: any[] }>('/query/personnel', params);
        console.log('listPersonnel response:', response.data);
        return Array.isArray(response.data.personnel) ? response.data.personnel : [];
    },

    createPersonnel: async (params: {
        person_id: string;
        tenant_id?: string;
        site_id?: string;
        name: string;
        role: string;
        phone?: string;
        email?: string;
        on_call?: boolean;
    }) => {
        const response = await api.post('/workflows/create_personnel', params);
        return response.data;
    },

    getCameraFullContext: async (cameraId: string, params: { tenant_id?: string; site_id?: string }) => {
        const response = await api.post('/query/camera-full-context', { camera_id: cameraId, ...params });
        return response.data;
    },

    listProfiles: async (params: { tenant_id?: string; site_id?: string }) => {
        const response = await api.post<{ detection_profiles: any[] }>('/query/profiles', params);
        console.log('listProfiles response:', response.data);
        return Array.isArray(response.data.detection_profiles) ? response.data.detection_profiles : []; // Unwrap nested list
    },

    createProfile: async (params: {
        profile_id: string;
        tenant_id?: string;
        site_id?: string;
        gateway_id?: string;
        name: string;
        targets: string[];
    }) => {
        const response = await api.post('/workflows/create_profile', params);
        return response.data;
    },

    updateProfile: async (params: {
        profile_id: string;
        tenant_id?: string;
        site_id?: string;
        gateway_id?: string;
        name?: string;
        targets?: string[];
    }) => {
        const response = await api.post('/workflows/update_profile', params);
        return response.data;
    },

    updateCamera: async (params: Partial<CreateCameraParams> & {
        assigned_model_id?: string;
        assigned_policy_id?: string;
        target_profile_ids?: string[];
    }) => {
        const response = await api.post('/workflows/update_camera', params);
        return response.data;
    },

    assignCamerasToModel: async (params: {
        tenant_id?: string;
        site_id?: string;
        gateway_id?: string;
        model_id: string;
        camera_ids: string[];
    }) => {
        // We don't have a direct endpoint for this tool yet, we should add it.
        // But for now let's assume we can add it to main.py
        const response = await api.post('/workflows/assign_cameras_to_model', params);
        return response.data;
    },

    configureMapper: async (gateway_id: string) => {
        const req: ConfigureMapperRequest = { gateway_id };
        const response = await api.post('/api/configure', req);
        return response.data;
    }
};

// --- Demo Mode Implementation ---
import { demoStore, DEMO_SITE_HEALTH, DEMO_MODELS, DEMO_POLICIES, DEMO_PROFILES, DEMO_PERSONNEL } from './demoData';

const demoQueries = {
    setupPPESite: async (_data: any) => ({ status: 'success', message: 'Demo Setup Complete' }),

    enablePPE: async (camera_id: string, _params?: any) => {
        demoStore.updateCameraStatus(camera_id, 'ACTIVE');
        return { status: 'success', message: `PPE Enabled for ${camera_id}` };
    },

    disablePPE: async (camera_id: string, _params?: any) => {
        demoStore.updateCameraStatus(camera_id, 'INACTIVE');
        return { status: 'success', message: `PPE Disabled for ${camera_id}` };
    },

    createCamera: async (params: CreateCameraParams) => {
        const newCam = demoStore.addCamera(params);
        return newCam;
    },

    getSiteHealth: async (_params: any) => {
        // Recalculate basic stats for realism
        const active = demoStore.cameras.filter(c => c.status === 'ACTIVE').length;
        const inactive = demoStore.cameras.filter(c => c.status !== 'ACTIVE').length;
        return {
            ...DEMO_SITE_HEALTH,
            cameras_active: active,
            cameras_inactive: inactive
        };
    },

    getStickyDefaults: async () => ({
        effective_defaults: { tenant_id: 'DEMO', site_id: 'DEMO_SITE', gateway_id: 'gw-demo-001' },
        last_used: { tenant_id: 'DEMO', site_id: 'DEMO_SITE', gateway_id: 'gw-demo-001' }
    }),

    listCameras: async (params: CameraRequest) => {
        console.log('[DEMO] Listing cameras', params);
        return demoStore.getCameras(params.gateway_id);
    },

    listGateways: async (_params: any) => {
        return demoStore.gateways;
    },

    listModels: async (_params: any) => DEMO_MODELS,

    createModel: async (params: any) => ({ ...params, status: 'READY' }),

    listPolicies: async (_params: any) => DEMO_POLICIES,

    createPolicy: async (params: any) => params,

    updatePolicy: async (params: any) => params,

    listPersonnel: async (_params: any) => DEMO_PERSONNEL,

    createPersonnel: async (params: any) => params,

    getCameraFullContext: async (cameraId: string, _params: any) => {
        const cam = demoStore.cameras.find(c => c.id === cameraId);
        return { camera: cam, model: DEMO_MODELS[0], policy: DEMO_POLICIES[0] };
    },

    listProfiles: async (_params: any) => DEMO_PROFILES,

    createProfile: async (params: any) => params,

    updateProfile: async (params: any) => params,

    updateCamera: async (params: any) => params,

    assignCamerasToModel: async (_params: any) => ({ success: true }),

    configureMapper: async (_gateway_id: string) => ({ success: true, message: 'Demo Mapper Configured' })
};

// --- Proxy to switch between Real and Demo ---
const isDemoMode = () => localStorage.getItem('DEMO_MODE') === 'true';

export const queries = new Proxy(realQueries, {
    get: (target, prop: keyof typeof realQueries) => {
        if (isDemoMode()) {
            // @ts-ignore - we know demoQueries has the same keys generally, or we fallback if missing?
            // Ideally they match exactly. For now assuming they do or typescript will catch it during build if we were strict.
            // Since we implemented all keys in demoQueries above matching realQueries keys:
            return (demoQueries as any)[prop];
        }
        return target[prop];
    }
});
