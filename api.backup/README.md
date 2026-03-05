# HMI CRUD API

A FastAPI-based REST API for managing HMI (Human-Machine Interface) resources including gateways, assets, models, personnel, policies, events, actions, and profiles.

## Features

- 🚀 **FastAPI Framework** - Modern, fast, async API framework
- 🗄️ **MongoDB Integration** - Async MongoDB driver (Motor)
- ✅ **Data Validation** - Pydantic models with strict validation
- 🔄 **Partial Updates** - Support for nested field updates with proper merging
- 📝 **Auto-generated Docs** - Interactive API documentation (Swagger/ReDoc)
- 🏷️ **Type Safety** - Full type hints throughout the codebase

## Project Structure

```
api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── db.py                # MongoDB connection management
│   ├── crud/
│   │   └── base.py          # Base CRUD operations
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   ├── assets.py
│   │   ├── gateway.py
│   │   ├── models.py
│   │   ├── personnel.py
│   │   ├── policies.py
│   │   ├── events.py
│   │   ├── actions.py
│   │   └── profiles.py
│   ├── schemas/             # Pydantic models
│   │   ├── common.py
│   │   ├── assets.py
│   │   ├── gateway.py
│   │   ├── models.py
│   │   ├── personnel.py
│   │   ├── policies.py
│   │   ├── events.py
│   │   ├── actions.py
│   │   └── profiles.py
│   └── utils.py             # Utility functions
├── requirements.txt         # Python dependencies
├── run_tests.py            # Comprehensive test suite
└── .env                    # Environment variables (not in git)
```

## Installation

### Prerequisites

- Python 3.10+
- MongoDB 4.4+

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate virtual environment**
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=hmi
   API_TITLE=HMI CRUD API
   API_VERSION=1.0.0
   ```

## Running the Application

### Development Server

```bash
uvicorn app.main:app --reload --port 8015
```

The API will be available at:
- **API Base URL**: http://localhost:8015
- **Interactive Docs (Swagger)**: http://localhost:8015/docs
- **Alternative Docs (ReDoc)**: http://localhost:8015/redoc

### Production Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8015 --workers 4
```

## API Endpoints

### Gateway Management
- `POST /gateway` - Create gateway
- `GET /gateway/{gateway_id}` - Get gateway by ID
- `PUT /gateway/{gateway_id}` - Update gateway
- `DELETE /gateway/{gateway_id}` - Delete gateway
- `GET /gateway` - List gateways with filters

### Asset Management
- `POST /assets` - Create asset
- `GET /assets/{asset_id}` - Get asset by ID
- `PUT /assets/{asset_id}` - Update asset (supports partial updates)
- `DELETE /assets/{asset_id}` - Delete asset
- `GET /assets` - List assets with filters

### Model Management
- `POST /models` - Create model
- `GET /models/{model_id}` - Get model by ID
- `PUT /models/{model_id}` - Update model
- `DELETE /models/{model_id}` - Delete model
- `GET /models` - List models with filters

### Personnel Management
- `POST /personnel` - Create personnel
- `GET /personnel/{personnel_id}` - Get personnel by ID
- `PUT /personnel/{personnel_id}` - Update personnel
- `DELETE /personnel/{personnel_id}` - Delete personnel
- `GET /personnel` - List personnel with filters

### Policy Management
- `POST /policies` - Create policy
- `GET /policies/{policy_id}` - Get policy by ID
- `PUT /policies/{policy_id}` - Update policy
- `DELETE /policies/{policy_id}` - Delete policy
- `GET /policies` - List policies with filters

### Event Management
- `POST /events` - Create event
- `GET /events/{event_id}` - Get event by ID
- `PUT /events/{event_id}` - Update event
- `DELETE /events/{event_id}` - Delete event
- `GET /events` - List events with filters

### Action Management
- `POST /actions` - Create action
- `GET /actions/{action_id}` - Get action by ID
- `PUT /actions/{action_id}` - Update action
- `DELETE /actions/{action_id}` - Delete action
- `GET /actions` - List actions with filters

### Profile Management
- `POST /profiles` - Create profile
- `GET /profiles/{profile_id}` - Get profile by ID
- `PUT /profiles/{profile_id}` - Update profile
- `DELETE /profiles/{profile_id}` - Delete profile
- `GET /profiles` - List profiles with filters

## Testing

Run the comprehensive test suite:

```bash
python run_tests.py
```

This will test:
- ✅ Asset CRUD operations with partial updates
- ✅ Model creation with timestamp validation
- ✅ Action creation with proper schema handling
- ✅ Gateway listing functionality

## Key Features

### Partial Updates with Field Merging

The API supports partial updates for nested objects. For example, updating only the FPS of a camera stream:

```json
PUT /assets/CAM_GATE3_001
{
  "asset_info": {
    "camera": {
      "stream": {
        "fps": 30
      }
    }
  }
}
```

This will update only the `fps` field while preserving all other fields like `rtsp_url`, `onvif_url`, `resolution`, etc.

### Automatic Timestamps

All resources automatically include:
- `created_at` - Timestamp when the resource was created
- `updated_at` - Timestamp of the last update

### Field Validation

All endpoints use Pydantic models for strict validation:
- Type checking
- Required field validation
- Extra field prevention (`extra = "forbid"`)
- Custom field constraints

## Database Schema

### Collections

- `gateway` - Gateway devices
- `assets` - Camera and sensor assets
- `models` - AI/ML models
- `personnel` - Personnel records
- `policies` - Security policies
- `events` - Detected events
- `actions` - Actions triggered by events
- `profiles` - Detection profiles

### Indexes

The application automatically creates indexes on startup for optimal query performance:
- Tenant/Site/Gateway composite indexes
- Status indexes
- Type and tag indexes for filtering
- Timestamp indexes for sorting

## Configuration

Environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB` | Database name | `hmi` |
| `API_TITLE` | API title for documentation | `HMI CRUD API` |
| `API_VERSION` | API version | `1.0.0` |

## Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints throughout
- Document complex functions with docstrings

### Adding New Endpoints

1. Create schema in `app/schemas/`
2. Create router in `app/routers/`
3. Add router to `ALL_ROUTERS` in `app/routers/__init__.py`
4. Add indexes in `app/main.py` if needed

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'app'`
- **Solution**: Make sure you're running from the project root and the virtual environment is activated

**Issue**: `pymongo.errors.ServerSelectionTimeoutError`
- **Solution**: Ensure MongoDB is running and accessible at the configured URI

**Issue**: 500 Internal Server Error on POST
- **Solution**: Check that all required fields are included and `_id` field is provided

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Contact

[Your Contact Information Here]
