/*** CREATE PersonalInfo ***/
async function create_personalInfo(req, res, next) {
  try {
    const PersonalInfo = req.app.locals.PersonalInfoModel;

    if (!PersonalInfo) {
      throw new Error('PersonalInfoModel is not initialized');
    }

    // Required fields
    const { _id, tenant_id, site_id, name, status } = req.body;
    if (!_id || !tenant_id || !site_id || !name) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: _id, tenant_id, site_id, name'
      });
    }

    // Optional fields
    const { role, contact, on_call } = req.body;

    const person = await PersonalInfo.create({
      _id,
      tenant_id,
      site_id,
      name,
      status: status || 'ACTIVE',
      role,
      contact,
      on_call
    });

    res.status(201).json({
      success: true,
      message: 'Personal Info created successfully',
      data: person.toObject({ versionKey: false }) // removes __v
    });

  } catch (err) {
    if (err.name === 'ValidationError') {
      return res.status(400).json({
        success: false,
        message: err.message,
        errors: err.errors
      });
    }
    next(err);
  }
}

/*** LIST Personal Info (all or filtered) ***/
async function list_personalInfo(req, res, next) {
  try {
  const PersonalInfo = req.app.locals.PersonalInfoModel;

    if (!PersonalInfo) {
      throw new Error('PersonalInfoModel is not initialized');
    }

    // Build a filter object from query parameters
    const filter = {};

    if (req.query._id) filter._id = req.query._id;
    if (req.query.tenant_id) filter.tenant_id = req.query.tenant_id;
    if (req.query.site_id) filter.site_id = req.query.site_id;
    if (req.query.status) filter.status = req.query.status;

    // If no query params, returns all gateways
    const personalinfo = await PersonalInfo.find(filter);

    res.status(200).json({
      success: true,
      count: personalinfo.length,
      data: personalinfo
    });
  } catch (error) {
    next(error);
  }
}



module.exports = {
  create_personalInfo,
  list_personalInfo
};

