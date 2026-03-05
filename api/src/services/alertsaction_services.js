/************************************************
 * CREATE Alert Action
 ************************************************/
async function create_alert_action(req, res, next) {
  try {
    const AlertAction = req.AlertActionModel;
    if (!AlertAction) {
      throw new Error('AlertAction model is not initialized');
    }

    const {
      _id,
      tenant_id,
      site_id,
      gateway_id,
      event_id,
      policy_id,
      route_severity,
      decisions
    } = req.body;

    // ---- Basic required validation ----
    if (
      !_id ||
      !tenant_id ||
      !site_id ||
      !gateway_id ||
      !event_id ||
      !policy_id ||
      !route_severity
    ) {
      return res.status(400).json({
        success: false,
        message:
          'Missing required fields: _id, tenant_id, site_id, gateway_id, event_id, policy_id, route_severity'
      });
    }

    const action = await AlertAction.create(req.body);

    res.status(201).json({
      success: true,
      message: 'Alert action created successfully',
      data: action
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * LIST Alert Actions (filterable)
 ************************************************/
async function list_alert_actions(req, res, next) {
  try {
    const AlertAction = req.AlertActionModel;
    if (!AlertAction) {
      throw new Error('AlertAction model is not initialized');
    }

    const filter = {};

    if (req.query._id) filter._id = req.query._id;
    if (req.query.tenant_id) filter.tenant_id = req.query.tenant_id;
    if (req.query.site_id) filter.site_id = req.query.site_id;
    if (req.query.gateway_id) filter.gateway_id = req.query.gateway_id;
    if (req.query.event_id) filter.event_id = req.query.event_id;
    if (req.query.policy_id) filter.policy_id = req.query.policy_id;

    const actions = await AlertAction
      .find(filter)
      .sort({ created_at: -1 });

    res.status(200).json({
      success: true,
      count: actions.length,
      data: actions
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * GET single Alert Action (by ID + tenant)
 ************************************************/
async function get_alert_action(req, res, next) {
  try {
    const AlertAction = req.AlertActionModel;
    if (!AlertAction) {
      throw new Error('AlertAction model is not initialized');
    }

    const { _id, tenant_id } = req.query;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: 'tenant_id and _id are required'
      });
    }

    const action = await AlertAction.findOne({ _id, tenant_id });

    if (!action) {
      return res.status(404).json({
        success: false,
        message: 'Alert action not found'
      });
    }

    res.status(200).json({
      success: true,
      data: action
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * UPDATE Alert Action (decisions / status)
 ************************************************/
async function update_alert_action(req, res, next) {
  try {
    const AlertAction = req.AlertActionModel;
    if (!AlertAction) {
      throw new Error('AlertAction model is not initialized');
    }

    const { _id, tenant_id } = req.body;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: '_id and tenant_id are required for update'
      });
    }

    const updated = await AlertAction.findOneAndUpdate(
      { _id, tenant_id },
      {
        ...req.body,
        updated_at: new Date()
      },
      { new: true }
    );

    if (!updated) {
      return res.status(404).json({
        success: false,
        message: 'Alert action not found'
      });
    }

    res.status(200).json({
      success: true,
      message: 'Alert action updated successfully',
      data: updated
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * DELETE Alert Action (OPTIONAL – audit sensitive)
 ************************************************/
async function delete_alert_action(req, res, next) {
  try {
    const AlertAction = req.AlertActionModel;
    if (!AlertAction) {
      throw new Error('AlertAction model is not initialized');
    }

    const { _id, tenant_id } = req.body;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: '_id and tenant_id are required'
      });
    }

    const result = await AlertAction.deleteOne({ _id, tenant_id });

    if (result.deletedCount === 0) {
      return res.status(404).json({
        success: false,
        message: 'Alert action not found'
      });
    }

    res.status(200).json({
      success: true,
      message: 'Alert action deleted successfully'
    });
  } catch (error) {
    next(error);
  }
}

module.exports = {
  create_alert_action,
  list_alert_actions,
  get_alert_action,
  update_alert_action,
  delete_alert_action
};
