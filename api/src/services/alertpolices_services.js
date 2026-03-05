/************************************************
 * CREATE Alert Policy
 ************************************************/
async function create_alert_policy(req, res, next) {
  try {
    const AlertPolicy = req.AlertPolicyModel;
    if (!AlertPolicy) {
      throw new Error('AlertPolicy model is not initialized');
    }

    const {
      _id,
      tenant_id,
      site_id,
      anomaly_type
    } = req.body;

    // ---- Required fields ----
    if (!_id || !tenant_id || !site_id || !anomaly_type) {
      return res.status(400).json({
        success: false,
        message:
          'Missing required fields: _id, tenant_id, site_id, anomaly_type'
      });
    }

    const policy = await AlertPolicy.create(req.body);

    res.status(201).json({
      success: true,
      message: 'Alert policy created successfully',
      data: policy
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * LIST Alert Policies (filterable)
 ************************************************/
async function list_alert_policies(req, res, next) {
  try {
    const AlertPolicy = req.AlertPolicyModel;
    if (!AlertPolicy) {
      throw new Error('AlertPolicy model is not initialized');
    }

    const filter = {};

    if (req.query._id) filter._id = req.query._id;
    if (req.query.tenant_id) filter.tenant_id = req.query.tenant_id;
    if (req.query.site_id) filter.site_id = req.query.site_id;
    if (req.query.anomaly_type) filter.anomaly_type = req.query.anomaly_type;
    if (req.query.enabled !== undefined)
      filter.enabled = req.query.enabled === 'true';

    const policies = await AlertPolicy
      .find(filter)
      .sort({ priority: -1, updated_at: -1 });

    res.status(200).json({
      success: true,
      count: policies.length,
      data: policies
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * GET single Alert Policy
 ************************************************/
async function get_alert_policy(req, res, next) {
  try {
    const AlertPolicy = req.AlertPolicyModel;
    if (!AlertPolicy) {
      throw new Error('AlertPolicy model is not initialized');
    }

    const { _id, tenant_id } = req.query;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: 'tenant_id and _id are required'
      });
    }

    const policy = await AlertPolicy.findOne({ _id, tenant_id });

    if (!policy) {
      return res.status(404).json({
        success: false,
        message: 'Alert policy not found'
      });
    }

    res.status(200).json({
      success: true,
      data: policy
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * UPDATE Alert Policy
 ************************************************/
async function update_alert_policy(req, res, next) {
  try {
    const AlertPolicy = req.AlertPolicyModel;
    if (!AlertPolicy) {
      throw new Error('AlertPolicy model is not initialized');
    }

    const { _id, tenant_id } = req.body;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: '_id and tenant_id are required for update'
      });
    }

    const updated = await AlertPolicy.findOneAndUpdate(
      { _id, tenant_id },
      req.body,
      { new: true }
    );

    if (!updated) {
      return res.status(404).json({
        success: false,
        message: 'Alert policy not found'
      });
    }

    res.status(200).json({
      success: true,
      message: 'Alert policy updated successfully',
      data: updated
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * DELETE Alert Policy
 ************************************************/
async function delete_alert_policy(req, res, next) {
  try {
    const AlertPolicy = req.AlertPolicyModel;
    if (!AlertPolicy) {
      throw new Error('AlertPolicy model is not initialized');
    }

    const { _id, tenant_id } = req.body;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: '_id and tenant_id are required'
      });
    }

    const result = await AlertPolicy.deleteOne({ _id, tenant_id });

    if (result.deletedCount === 0) {
      return res.status(404).json({
        success: false,
        message: 'Alert policy not found'
      });
    }

    res.status(200).json({
      success: true,
      message: 'Alert policy deleted successfully'
    });
  } catch (error) {
    next(error);
  }
}

module.exports = {
  create_alert_policy,
  list_alert_policies,
  get_alert_policy,
  update_alert_policy,
  delete_alert_policy
};
