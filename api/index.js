require('dotenv').config();
const express = require('express');
const cors = require('cors');
const compression = require('compression');

const { connectDatabases, connections } = require('./src/config/database');
const createAssetModel = require('./src/models/assets.model');
const createGatewayModel = require('./src/models/gateway.model');
const createPersonalInfoModel = require('./src/models/personal.model');
const createAiModel = require('./src/models/aimodel.model');
const createAlertActionModel = require('./src/models/alertaction.model');
const createAlertPolicyModel = require('./src/models/alertpolices.model');
const createAnomalyEventModel = require('./src/models/anamoly.model');
const createProfileModel = require('./src/models/profile.model');
async function startServer() {
  const app = express();
  const PORT = process.env.PORT || 3000;

  try {
    // 1️⃣ Connect DBs
    await connectDatabases();

    // 2️⃣ Create models AFTER DB connection
    const AssetModel = createAssetModel(connections.assetsDB);
    const GatewayModel = createGatewayModel(connections.gatewaysDB);
    const PersonalInfoModel = createPersonalInfoModel(connections.assetsDB);
    const AiModel = createAiModel(connections.assetsDB);
    const AlertActionModel = createAlertActionModel(connections.gatewaysDB);
    const AlertPolicyModel = createAlertPolicyModel(connections.gatewaysDB);
    const AnomalyEventModel = createAnomalyEventModel(connections.gatewaysDB);
    const ProfileModel = createProfileModel(connections.assetsDB);

    // 3️⃣ Store models in app.locals
    app.locals.AssetModel = AssetModel;
    app.locals.GatewayModel = GatewayModel;
    app.locals.PersonalInfoModel = PersonalInfoModel;
    app.locals.AiModel = AiModel;
    app.locals.AlertActionModel = AlertActionModel
    app.locals.AlertPolicyModel = AlertPolicyModel;
    app.locals.AnomalyEventModel = AnomalyEventModel;
    app.locals.ProfileModel = ProfileModel;

 

    // 4️⃣ Middleware
    app.use(cors());
    app.use(compression()); // Enable gzip compression
    app.use(express.json({ limit: '10mb' })); // Set size limit
    app.use(express.urlencoded({ extended: true, limit: '10mb' }));
    // Cache disabled - causing slowdown
    // app.use(cacheMiddleware);           // Cache GET responses
    // app.use(clearCacheOnWrite);         // Clear cache on write operations

    // 5️⃣ Attach routes AFTER models exist
    const router = require('./routes/router'); // require here, after models
    app.use('/', router);

    // 6️⃣ Health check
    app.get('/health', (req, res) => res.status(200).json({ status: 'OK' }));

    // 7️⃣ Global error handler
    app.use((err, req, res, next) => {
      console.error('Global Error:', err);
      res.status(500).json({ success: false, message: err.message });
    });

    // 8️⃣ Start server
    app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

  } catch (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }
}

startServer();
