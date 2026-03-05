const mongoose = require('mongoose');

// ---------- Sub-schemas ----------

// Target inside routes
const RouteTargetSchema = new mongoose.Schema(
  {
    target_type: {
      type: String,
      enum: ['ROLE', 'PERSON'],
      required: true
    },
    value: { type: String, required: true }
  },
  { _id: false }
);

// Route schema
const AlertRouteSchema = new mongoose.Schema(
  {
    severity: {
      type: String,
      enum: ['INFO', 'WARNING', 'CRITICAL'],
      required: true
    },
    targets: {
      type: [RouteTargetSchema],
      default: []
    },
    channels: {
      type: [String],
      default: []
    }
  },
  { _id: false }
);

// ---------- Main schema ----------
const AlertPolicySchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },

    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },

    anomaly_type: { type: String, required: true },

    min_severity: {
      type: String,
      enum: ['INFO', 'WARNING', 'CRITICAL'],
      default: 'INFO'
    },

    enabled: { type: Boolean, default: true },

    priority: { type: Number, default: 0 },

    routes: {
      type: [AlertRouteSchema],
      default: []
    },

    created_at: { type: Date, default: Date.now },
    updated_at: { type: Date, default: Date.now }
  },
  {
    versionKey: false
  }
);

// ---------- Hooks ----------
AlertPolicySchema.pre('save', function () {
  this.updated_at = new Date();
});

AlertPolicySchema.pre('findOneAndUpdate', function () {
  this.set({ updated_at: new Date() });
});

// ---------- Export model factory ----------
module.exports = (connection) => {
  if (connection.models.AlertPolicy)
    return connection.models.AlertPolicy;

  return connection.model('AlertPolicy', AlertPolicySchema);
};
