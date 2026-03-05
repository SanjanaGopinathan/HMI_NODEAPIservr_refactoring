/*** CREATE AiModel ***/
async function create_aimodel(req, res, next) {
  try {
    const AiModels = req.app.locals.AiModel;

    if (!AiModels) {
      throw new Error('AiModel is not initialized');
    }

    // Required fields
    const { _id, tenant_id, site_id, gateway_id, status } = req.body;
    if (!_id || !tenant_id || !site_id || !gateway_id) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: _id, tenant_id, site_id, gateway_id'
      });
    }

    // Optional fields
    const { name, framework_id, supported_profile_ids } = req.body;

    const person = await AiModels.create({
      _id,
      tenant_id,
      site_id,
      gateway_id,
      name,
      status: status || 'ACTIVE',
      framework_id,
      supported_profile_ids,
    });

    res.status(201).json({
      success: true,
      message: 'AI Model created successfully',
      data: person.toObject({ versionKey: false })
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

/*** LIST of AI Models (all or filtered) ***/
async function list_aimodels(req, res, next) {
  try {
  const AiModels = req.app.locals.AiModel;

    if (!AiModels) {
      throw new Error('AiModels is not initialized');
    }

    // Build a filter object from query parameters
    const filter = {};

    if (req.query._id) filter._id = req.query._id;
    if (req.query.tenant_id) filter.tenant_id = req.query.tenant_id;
    if (req.query.site_id) filter.site_id = req.query.site_id;
    if (req.query.gateway_id) filter.gateway_id = req.query.gateway_id;

    if (req.query.status) filter.status = req.query.status;

    // If no query params, returns all gateways
    const modelList = await AiModels.find(filter);

    res.status(200).json({
      success: true,
      count: modelList.length,
      data: modelList
    });
  } catch (error) {
    next(error);
  }
}




module.exports = {
  create_aimodel,
  list_aimodels
  
};

