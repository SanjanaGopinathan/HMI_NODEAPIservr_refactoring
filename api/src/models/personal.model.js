const mongoose = require('mongoose');

const PersonalInfoSchema = new mongoose.Schema(
  {
    _id: { type: String, required: true },
    tenant_id: { type: String, required: true },
    site_id: { type: String, required: true },
    name: String,
    role: String,

    contact: {
      phone: {
        type: String,
        trim: true
      },
      email: {
        type: String,
        lowercase: true,
        trim: true,
        match: [/^\S+@\S+\.\S+$/, 'Invalid email address']
      },
      sip_uri: String
    },

    on_call: {
      type: Boolean,
      default: false
    },

    status: {
      type: String,
      enum: ['ACTIVE', 'INACTIVE'],
      default: 'ACTIVE'
    }
  },
  {
    timestamps: {
      createdAt: 'created_at',
      updatedAt: 'updated_at'
    },
    versionKey: false 
  }
);

PersonalInfoSchema.pre('save', function () {
  this.updated_at = new Date();
});

module.exports = (connection) => {
  if (connection.models.PersonalInfo) {
    return connection.models.PersonalInfo;
  }
  return connection.model('PersonalInfo', PersonalInfoSchema);
};
