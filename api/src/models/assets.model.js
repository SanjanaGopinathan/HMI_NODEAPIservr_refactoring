const mongoose = require('mongoose');
const { connections } = require('../config/database');

// ---------- Sub-schema ----------
const AssetInfoSchema = new mongoose.Schema(
  {
    asset_type: String,
    capabilities: [String],
    camera: {
      stream: {
        rtsp_url: String,
        onvif_url: String,
        fps: Number
      },
      resolution: String
    },
    bindings: {
      assigned_model_id: String,
      target_profile_ids: [String],
      assigned_policy_id: String
    },
    tags: [String]
  },
  { _id: false }
);

// ---------- Main schema ----------
const AssetSchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },
    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },
    gateway_id: { type: String, required: true },
    name: { type: String, required: true },
    location: String,
    zone: String,
    status: String,
    asset_info: AssetInfoSchema,
    created_at: { type: Date, default: Date.now },
    updated_at: { type: Date, default: Date.now }
  },
  { versionKey: false }
);

// Auto-update updated_at
AssetSchema.pre('save', function () {
  this.updated_at = new Date();
});

// Export a function to create the model on a given connection
module.exports = (connection) => {
  return connection.model('Asset', AssetSchema);
};