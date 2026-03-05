const mongoose = require('mongoose');
const { connections } = require('../config/database');



const AiModelSchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },
    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },
    gateway_id: { type: String, required: true },
    name: String,
    framework_id: { type: String, required: true },
    supported_profile_ids: [String],
    status: {
      type: String,
      enum: ['ACTIVE', 'INACTIVE'],
      default: 'ACTIVE'
    },
    created_at: { type: Date, default: Date.now },
    updated_at: { type: Date, default: Date.now }
  },
  {
    versionKey: false
  }
);




AiModelSchema.pre('save', function () {
  this.updated_at = new Date();
});


// Export a function to create the model on a given connection
module.exports = (connection) => {
  if (connection.models.AiModel) {
    return connection.models.AiModel;
  }
  return connection.model('AiModel', AiModelSchema);
};