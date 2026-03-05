const mongoose = require('mongoose');

const ProfileSchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },
    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },
    gateway_id: { type: String, required: true },
    name: { type: String, required: true },
    targets: [String],
    created_at: { type: Date, default: Date.now },
    updated_at: { type: Date, default: Date.now }
  },
  { versionKey: false }
);

ProfileSchema.pre('save', function () {
  this.updated_at = new Date();
});

module.exports = (connection) => {
  if (connection.models.Profile) {
    return connection.models.Profile;
  }
  return connection.model('Profile', ProfileSchema);
};
