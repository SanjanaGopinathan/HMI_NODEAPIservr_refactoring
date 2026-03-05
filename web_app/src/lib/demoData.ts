import type { SiteHealth, Camera, CreateCameraParams } from './api';

export const DEMO_GATEWAYS = [
    {
        _id: 'gw-demo-001',
        name: 'Main Entrance Gateway',
        status: 'ONLINE',
        last_seen_at: new Date().toISOString(),
        hmi: { base_url: 'http://192.168.1.100' }
    },
    {
        _id: 'gw-demo-002',
        name: 'Warehouse East Gateway',
        status: 'OFFLINE',
        last_seen_at: new Date(Date.now() - 86400000).toISOString(),
        hmi: { base_url: 'http://192.168.1.101' }
    }
];

export const DEMO_CAMERAS: Camera[] = [
    {
        id: 'cam-demo-001',
        name: 'Front Lobby',
        rtsp_url: 'rtsp://demo/stream1',
        location: 'Lobby',
        status: 'ACTIVE'
    },
    {
        id: 'cam-demo-002',
        name: 'Loading Dock A',
        rtsp_url: 'rtsp://demo/stream2',
        location: 'Warehouse',
        status: 'ACTIVE'
    },
    {
        id: 'cam-demo-003',
        name: 'Server Room',
        rtsp_url: 'rtsp://demo/stream3',
        location: 'IT Wing',
        status: 'INACTIVE'
    },
    {
        id: 'cam-demo-004',
        name: 'Parking Lot',
        rtsp_url: 'rtsp://demo/stream4',
        location: 'Exterior',
        status: 'ACTIVE'
    }
];

export const DEMO_SITE_HEALTH: SiteHealth = {
    health_score: 92,
    cameras_active: 3,
    cameras_inactive: 1,
    cameras_without_model: ['cam-demo-003'],
    cameras_without_policy: [],
    cameras_without_profiles: [],
    recommendations: [
        'Camera "Server Room" is inactive.',
        'Consider adding redundancy for "Warehouse East Gateway".'
    ],
    issues: [
        'Gateway "gw-demo-002" is offline.'
    ]
};

export const DEMO_MODELS = [
    { _id: 'model-demo-001', name: 'Standard PPE Detection', framework_id: 'yolov8', status: 'READY' },
    { _id: 'model-demo-002', name: 'Face Recognition', framework_id: 'facenet', status: 'LOADING' }
];

export const DEMO_POLICIES = [
    { _id: 'pol-demo-001', anomaly_type: 'No Helmet', severity_levels: ['CRITICAL'], enabled: true },
    { _id: 'pol-demo-002', anomaly_type: 'Unauthorized Access', severity_levels: ['HIGH'], enabled: true }
];

export const DEMO_PROFILES = [
    { _id: 'prof-demo-001', name: 'Day Shift Specs', targets: ['helmet', 'vest'] },
    { _id: 'prof-demo-002', name: 'Night Shift Specs', targets: ['person'] }
];

export const DEMO_PERSONNEL = [
    { _id: 'pers-demo-001', name: 'John Doe', role: 'Security Manager', phone: '555-0100', on_call: true },
    { _id: 'pers-demo-002', name: 'Jane Smith', role: 'Site Admin', phone: '555-0102', on_call: false }
];

// Simple in-memory storage for the current session
class DemoStore {
    cameras: Camera[];
    gateways: any[];

    constructor() {
        this.cameras = [...DEMO_CAMERAS];
        this.gateways = [...DEMO_GATEWAYS];
    }

    getCameras(gateway_id?: string) {
        // In a real app we filter by gateway, for demo we just return all if gateway matches our demo ones
        if (gateway_id && !this.gateways.find(g => g._id === gateway_id)) return [];
        return this.cameras;
    }

    updateCameraStatus(id: string, status: string) {
        this.cameras = this.cameras.map(c => c.id === id ? { ...c, status } : c);
        return this.cameras.find(c => c.id === id);
    }

    addCamera(params: CreateCameraParams) {
        const newCam: Camera = {
            id: params.camera_id || `cam-demo-${Date.now()}`,
            name: params.name,
            rtsp_url: params.rtsp_url,
            location: params.location || 'Unknown',
            status: 'INACTIVE' // Default to inactive
        };
        this.cameras.push(newCam);
        return newCam;
    }
}

export const demoStore = new DemoStore();
