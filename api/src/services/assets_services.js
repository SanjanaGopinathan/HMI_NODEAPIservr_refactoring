/*** CREATE assets / cameras ***/
async function create_asset(req, res, next) {
  try {
    const Asset = req.AssetModel; // Get the model from request
    if (!Asset) {
      throw new Error('Asset model is not initialized');
    }

    const { _id, name, tenant_id, site_id, gateway_id } = req.body;

    if (!_id || !name || !tenant_id || !site_id || !gateway_id) {
      return res.status(400).json({
        success: false,
        message: 'Missing required fields: _id, name, tenant_id, site_id, gateway_id',
      });
    }

    // Save asset to the correct DB
    const asset = await Asset.create(req.body);

    res.status(201).json({
      success: true,
      message: 'Asset created successfully',
      data: asset,
    });
  } catch (error) {
    next(error); // pass to global error handler
  }
}

/*** LIST assets (all or filtered) ***/
async function list_assets(req, res, next) {
  try {
    const Asset = req.AssetModel;
    if (!Asset) throw new Error('Asset model is not initialized');

    // Build a filter from POST body if present, otherwise from query params.
    const source = req.body && Object.keys(req.body).length > 0 ? req.body : req.query;
    const filter = {};

    if (source._id) filter._id = source._id;
    if (source.tenant_id) filter.tenant_id = source.tenant_id;
    if (source.site_id) filter.site_id = source.site_id;
    if (source.gateway_id) filter.gateway_id = source.gateway_id;
    if (source.status) filter.status = source.status;

    console.log('Asset filter:', filter);

    // If no query parameters, it will return all documents
    console.time('[PERF] Asset.find()');
    const assets = await Asset.find(filter);
    console.timeEnd('[PERF] Asset.find()');
    console.log(`[PERF] Returned ${assets.length} assets`);

    res.status(200).json({
      success: true,
      count: assets.length,
      data: assets,
    });
  } catch (error) {
    next(error);
  }
}


module.exports = { create_asset, list_assets };
