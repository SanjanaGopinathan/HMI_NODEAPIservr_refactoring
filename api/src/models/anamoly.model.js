const mongoose = require('mongoose');

// ---------- Sub-schemas ----------

// Detection inside raw.detections
const DetectionSchema = new mongoose.Schema(
  {
    label: { type: String, required: true },
    confidence: { type: Number, required: true }
  },
  { _id: false }
);

// Raw payload schema
const RawEventSchema = new mongoose.Schema(
  {
    model_id: { type: String, required: true },
    detections: {
      type: [DetectionSchema],
      default: []
    }
  },
  { _id: false }
);

// ---------- Main schema ----------
const EventSchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },

    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },

    gateway_id: { type: String, required: true },
    sensor_id: { type: String, required: true },

    anomaly_type: { type: String, required: true },

    severity: {
      type: String,
      enum: ['INFO', 'WARNING', 'CRITICAL'],
      required: true
    },

    detected_at: { type: Date, required: true },

    raw: RawEventSchema,

    status: {
      type: String,
      enum: ['OPEN', 'ACKNOWLEDGED', 'RESOLVED'],
      default: 'OPEN'
    }
  },
  {
    versionKey: false
  }
);

// ---------- Indexes (important for scale) ----------
EventSchema.index({ tenant_id: 1, detected_at: -1 });
EventSchema.index({ tenant_id: 1, gateway_id: 1 });
EventSchema.index({ tenant_id: 1, status: 1 });

// ---------- Export model factory ----------
module.exports = (connection) => {
  if (connection.models.Event)
    return connection.models.Event;

  return connection.model('AnomalyEvent', EventSchema);
};
