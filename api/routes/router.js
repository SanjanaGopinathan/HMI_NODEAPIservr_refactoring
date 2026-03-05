const express = require('express');
const router = express.Router();
const AssetService = require('../src/services/assets_services');
const GatewayService = require('../src/services/gateway_services');
const PersonalService = require('../src/services/personal_services');
const AiModelService = require('../src/services/aimodel_services');
const AnomalyEventService = require('../src/services/anamoly_services');
const AlertPolicyService = require('../src/services/alertpolices_services');
const AlertActionService = require('../src/services/alertsaction_services');

// ==================== ASSETS ====================
// POST /assets - Create asset
router.post('/assets', (req, res, next) => {
  req.AssetModel = req.app.locals.AssetModel;
  AssetService.create_asset(req, res, next);
});

// GET /assets - List assets with filters
router.get('/assets', (req, res, next) => {
  req.AssetModel = req.app.locals.AssetModel;
  AssetService.list_assets(req, res, next);
});

// GET /assets/:id - Get single asset
router.get('/assets/:id', async (req, res) => {
  try {
    const AssetModel = req.app.locals.AssetModel;
    const asset = await AssetModel.findById(req.params.id);
    if (!asset) {
      return res.status(404).json({ error: 'Asset not found' });
    }
    res.json(asset);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// PUT /assets/:id - Update asset
router.put('/assets/:id', async (req, res) => {
  try {
    const AssetModel = req.app.locals.AssetModel;
    const asset = await AssetModel.findByIdAndUpdate(
      req.params.id,
      { $set: req.body },
      { new: true }
    );
    if (!asset) {
      return res.status(404).json({ error: 'Asset not found' });
    }
    res.json(asset);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// DELETE /assets/:id - Delete asset
router.delete('/assets/:id', async (req, res) => {
  try {
    const AssetModel = req.app.locals.AssetModel;
    const result = await AssetModel.findByIdAndDelete(req.params.id);
    if (!result) {
      return res.status(404).json({ error: 'Asset not found' });
    }
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== GATEWAYS ====================
// POST /gateway - Create gateway
router.post('/gateway', (req, res, next) => {
  req.GatewayModel = req.app.locals.GatewayModel;
  GatewayService.create_gateway(req, res, next);
});

// GET /gateway - List gateways
router.get('/gateway', (req, res, next) => {
  req.GatewayModel = req.app.locals.GatewayModel;
  GatewayService.list_gateways(req, res, next);
});

// GET /gateway/:id - Get single gateway
router.get('/gateway/:id', async (req, res) => {
  try {
    const GatewayModel = req.app.locals.GatewayModel;
    const gateway = await GatewayModel.findById(req.params.id);
    if (!gateway) {
      return res.status(404).json({ error: 'Gateway not found' });
    }
    res.json(gateway);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// PUT /gateway/:id - Update gateway
router.put('/gateway/:id', async (req, res) => {
  try {
    const GatewayModel = req.app.locals.GatewayModel;
    const gateway = await GatewayModel.findByIdAndUpdate(
      req.params.id,
      { $set: req.body },
      { new: true }
    );
    if (!gateway) {
      return res.status(404).json({ error: 'Gateway not found' });
    }
    res.json(gateway);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== MODELS ====================
// POST /models - Create model
router.post('/models', (req, res, next) => {
  req.AiModel = req.app.locals.AiModel;
  AiModelService.create_aimodel(req, res, next);
});

// GET /models - List models
router.get('/models', (req, res, next) => {
  req.AiModel = req.app.locals.AiModel;
  AiModelService.list_aimodels(req, res, next);
});

// GET /models/:id - Get single model
router.get('/models/:id', async (req, res) => {
  try {
    const AiModel = req.app.locals.AiModel;
    const model = await AiModel.findById(req.params.id);
    if (!model) {
      return res.status(404).json({ error: 'Model not found' });
    }
    res.json(model);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// DELETE /models/:id - Delete model
router.delete('/models/:id', async (req, res) => {
  try {
    const AiModel = req.app.locals.AiModel;
    const result = await AiModel.findByIdAndDelete(req.params.id);
    if (!result) {
      return res.status(404).json({ error: 'Model not found' });
    }
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== POLICIES ====================
// POST /policies - Create policy
router.post('/policies', (req, res, next) => {
  req.AlertPolicyModel = req.app.locals.AlertPolicyModel;
  AlertPolicyService.create_alert_policy(req, res, next);
});

// GET /policies - List policies
router.get('/policies', (req, res, next) => {
  req.AlertPolicyModel = req.app.locals.AlertPolicyModel;
  AlertPolicyService.list_alert_policies(req, res, next);
});

// GET /policies/:id - Get single policy
router.get('/policies/:id', async (req, res) => {
  try {
    const AlertPolicyModel = req.app.locals.AlertPolicyModel;
    const policy = await AlertPolicyModel.findById(req.params.id);
    if (!policy) {
      return res.status(404).json({ error: 'Policy not found' });
    }
    res.json(policy);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// PUT /policies/:id - Update policy
router.put('/policies/:id', (req, res, next) => {
  req.AlertPolicyModel = req.app.locals.AlertPolicyModel;
  AlertPolicyService.update_alert_policy(req, res, next);
});

// DELETE /policies/:id - Delete policy
router.delete('/policies/:id', (req, res, next) => {
  req.AlertPolicyModel = req.app.locals.AlertPolicyModel;
  AlertPolicyService.delete_alert_policy(req, res, next);
});

// ==================== PROFILES ====================
// POST /profiles - Create profile
router.post('/profiles', async (req, res) => {
  try {
    const ProfileModel = req.app.locals.ProfileModel;
    const profile = new ProfileModel(req.body);
    const result = await profile.save();
    res.status(201).json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET /profiles - List profiles
router.get('/profiles', async (req, res) => {
  try {
    const ProfileModel = req.app.locals.ProfileModel;
    const profiles = await ProfileModel.find();
    res.json(profiles);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET /profiles/:id - Get single profile
router.get('/profiles/:id', async (req, res) => {
  try {
    const ProfileModel = req.app.locals.ProfileModel;
    const profile = await ProfileModel.findById(req.params.id);
    if (!profile) {
      return res.status(404).json({ error: 'Profile not found' });
    }
    res.json(profile);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// PUT /profiles/:id - Update profile
router.put('/profiles/:id', async (req, res) => {
  try {
    const ProfileModel = req.app.locals.ProfileModel;
    const profile = await ProfileModel.findByIdAndUpdate(
      req.params.id,
      { $set: req.body },
      { new: true }
    );
    if (!profile) {
      return res.status(404).json({ error: 'Profile not found' });
    }
    res.json(profile);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// DELETE /profiles/:id - Delete profile
router.delete('/profiles/:id', async (req, res) => {
  try {
    const ProfileModel = req.app.locals.ProfileModel;
    const result = await ProfileModel.findByIdAndDelete(req.params.id);
    if (!result) {
      return res.status(404).json({ error: 'Profile not found' });
    }
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== PERSONNEL ====================
// POST /personnel - Create personnel
router.post('/personnel', (req, res, next) => {
  req.PersonnelInfoModel = req.app.locals.PersonalInfoModel;
  PersonalService.create_personalInfo(req, res, next);
});

// GET /personnel - List personnel
router.get('/personnel', (req, res, next) => {
  req.PersonnelInfoModel = req.app.locals.PersonalInfoModel;
  PersonalService.list_personalInfo(req, res, next);
});

// GET /personnel/:id - Get single personnel
router.get('/personnel/:id', async (req, res) => {
  try {
    const PersonalInfoModel = req.app.locals.PersonalInfoModel;
    const personnel = await PersonalInfoModel.findById(req.params.id);
    if (!personnel) {
      return res.status(404).json({ error: 'Personnel not found' });
    }
    res.json(personnel);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// ==================== EVENTS ====================
// POST /events - Create event
router.post('/events', (req, res, next) => {
  req.AnomalyEventModel = req.app.locals.AnomalyEventModel;
  AnomalyEventService.create_event(req, res, next);
});

// GET /events - List events
router.get('/events', (req, res, next) => {
  req.AnomalyEventModel = req.app.locals.AnomalyEventModel;
  AnomalyEventService.list_events(req, res, next);
});

// PUT /events/:id - Update event
router.put('/events/:id', (req, res, next) => {
  req.AnomalyEventModel = req.app.locals.AnomalyEventModel;
  AnomalyEventService.update_event(req, res, next);
});

// DELETE /events/:id - Delete event
router.delete('/events/:id', (req, res, next) => {
  req.AnomalyEventModel = req.app.locals.AnomalyEventModel;
  AnomalyEventService.delete_event(req, res, next);
});

// ==================== ACTIONS ====================
// POST /actions - Create action
router.post('/actions', (req, res, next) => {
  req.AlertActionModel = req.app.locals.AlertActionModel;
  AlertActionService.create_alert_action(req, res, next);
});

// GET /actions - List actions
router.get('/actions', (req, res, next) => {
  req.AlertActionModel = req.app.locals.AlertActionModel;
  AlertActionService.list_alert_actions(req, res, next);
});

// PUT /actions/:id - Update action
router.put('/actions/:id', (req, res, next) => {
  req.AlertActionModel = req.app.locals.AlertActionModel;
  AlertActionService.update_alert_action(req, res, next);
});

// DELETE /actions/:id - Delete action
router.delete('/actions/:id', (req, res, next) => {
  req.AlertActionModel = req.app.locals.AlertActionModel;
  AlertActionService.delete_alert_action(req, res, next);
});

// ==================== HEALTH CHECK ====================
router.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'Node.js API Server' });
});

module.exports = router;
