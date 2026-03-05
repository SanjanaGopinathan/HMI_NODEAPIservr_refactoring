/*** CREATE Gateway ***/

async function create_gateway(req, res, next) {
  try {
    const { _id, name, tenant_id, site_id, status } = req.body;

    // Validate required fields
    if (!_id || !name || !tenant_id || !site_id || !status) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: _id, name, tenant_id, site_id, status',
      });
    }

    // Create gateway document
    const gateway = await Gateway.create(req.body);

    res.status(201).json({
      success: true,
      message: 'Gateway created successfully',
      data: gateway,
    });
  } catch (error) {
    next(error); // pass to global error handler
  }
}

/*** LIST gateways (all or filtered) ***/
async function list_gateways(req, res, next) {
  try {
    const Gateway = req.GatewayModel; // Use the model from request/app.locals
    if (!Gateway) throw new Error('Gateway model is not initialized');

    // Build a filter object from query parameters
    const filter = {};

    if (req.query._id) filter._id = req.query._id;
    if (req.query.tenant_id) filter.tenant_id = req.query.tenant_id;
    if (req.query.site_id) filter.site_id = req.query.site_id;
    if (req.query.ip) filter.ip = req.query.ip;
    if (req.query.status) filter.status = req.query.status;

    // If no query params, returns all gateways
    const gateways = await Gateway.find(filter);

    res.status(200).json({
      success: true,
      count: gateways.length,
      data: gateways
    });
  } catch (error) {
    next(error);
  }
}


module.exports = {
  create_gateway,
  list_gateways
};

