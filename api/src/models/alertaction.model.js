const mongoose = require('mongoose');

// ---------- Sub-schemas ----------

// Target (ROLE / PERSON)
const TargetSchema = new mongoose.Schema(
  {
    type: {
      type: String,
      enum: ['ROLE', 'PERSON'],
      required: true
    },
    value: { type: String, required: true }
  },
  { _id: false }
);

// Address (EMAIL / PHONE / SIP / etc.)
const AddressSchema = new mongoose.Schema(
  {
    type: {
      type: String,
      enum: ['EMAIL', 'PHONE', 'SIP'],
      required: true
    },
    address: { type: String, required: true }
  },
  { _id: false }
);

// Decision per channel
const DecisionSchema = new mongoose.Schema(
  {
    channel: {
      type: String,
      enum: ['HMI_POPUP', 'EMAIL', 'PHONE_CALL', 'SIP_PTT'],
      required: true
    },

    target: TargetSchema,

    resolved_person_id: { type: String },

    address: AddressSchema,

    status: {
      type: String,
      enum: ['PENDING', 'SENT', 'FAILED'],
      default: 'PENDING'
    },

    sent_at: { type: Date }
  },
  { _id: false }
);

// ---------- Main schema ----------
const AlertActionSchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },

    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },

    gateway_id: { type: String, required: true },

    event_id: { type: String, required: true },
    policy_id: { type: String, required: true },

    route_severity: {
      type: String,
      enum: ['INFO', 'WARNING', 'CRITICAL'],
      required: true
    },

    decisions: {
      type: [DecisionSchema],
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
AlertActionSchema.pre('save', function () {
  this.updated_at = new Date();
});

// ---------- Indexes (very important) ----------
AlertActionSchema.index({ tenant_id: 1, event_id: 1 });
AlertActionSchema.index({ tenant_id: 1, policy_id: 1 });
AlertActionSchema.index({ tenant_id: 1, gateway_id: 1 });
AlertActionSchema.index({ tenant_id: 1, created_at: -1 });

// ---------- Export model factory ----------
module.exports = (connection) => {
  if (connection.models.AlertAction)
    return connection.models.AlertAction;

  return connection.model('AlertAction', AlertActionSchema);
};
