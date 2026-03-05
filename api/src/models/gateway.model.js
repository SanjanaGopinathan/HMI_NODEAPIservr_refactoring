const mongoose = require('mongoose');
const { connections } = require('../config/database');

// ---------- Sub-schema ----------
const HMISchema = new mongoose.Schema(
  {
    base_url: { type: String, required: true },
    health_path: { type: String, required: true }
  },
  { _id: false }
);

// ---------- Main schema ----------
const GatewaySchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },
    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },
    name: { type: String, required: true },
    hmi: HMISchema,
    status: {
      type: String,
      enum: ['ONLINE', 'OFFLINE', 'UNKNOWN'],
      default: 'UNKNOWN'
    },
    last_seen_at: Date,
    capabilities: [String],
    created_at: { type: Date, default: Date.now },
    updated_at: { type: Date, default: Date.now }
  },
  { versionKey: false }
);

GatewaySchema.pre('save', function () {
  this.updated_at = new Date();
});


// Export a function to create the model on a given connection
module.exports = (connection) => {
  // If model exists, return it
  if (connection.models.Gateway) return connection.models.Gateway;
  return connection.model('Gateway', GatewaySchema);
};