/************************************************
 * CREATE Event (Anomaly)
 ************************************************/
async function create_event(req, res, next) {
  try {
    const Event = req.AnomalyEventModel;
    if (!Event) {
      throw new Error('Event model is not initialized');
    }

    const {
      _id,
      tenant_id,
      site_id,
      gateway_id,
      sensor_id,
      anomaly_type,
      severity,
      detected_at
    } = req.body;

    // ---- Basic required validation ----
    if (
      !_id ||
      !tenant_id ||
      !site_id ||
      !gateway_id ||
      !sensor_id ||
      !anomaly_type ||
      !severity ||
      !detected_at
    ) {
      return res.status(400).json({
        success: false,
        message:
          'Missing required fields: _id, tenant_id, site_id, gateway_id, sensor_id, anomaly_type, severity, detected_at'
      });
    }

    const event = await Event.create(req.body);

    res.status(201).json({
      success: true,
      message: 'Event created successfully',
      data: event
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * LIST Events (filterable)
 ************************************************/
async function list_events(req, res, next) {
  try {
    const Event = req.AnomalyEventModel;
    if (!Event) {
      throw new Error('Event model is not initialized');
    }

    const filter = {};

    if (req.query._id) filter._id = req.query._id;
    if (req.query.tenant_id) filter.tenant_id = req.query.tenant_id;
    if (req.query.site_id) filter.site_id = req.query.site_id;
    if (req.query.gateway_id) filter.gateway_id = req.query.gateway_id;
    if (req.query.sensor_id) filter.sensor_id = req.query.sensor_id;
    if (req.query.anomaly_type) filter.anomaly_type = req.query.anomaly_type;
    if (req.query.severity) filter.severity = req.query.severity;
    if (req.query.status) filter.status = req.query.status;

    const events = await Event
      .find(filter)
      .sort({ detected_at: -1 });

    res.status(200).json({
      success: true,
      count: events.length,
      data: events
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * GET single Event (by ID + tenant)
 ************************************************/
async function get_event(req, res, next) {
  try {
    const Event = req.AnomalyEventModel;
    if (!Event) {
      throw new Error('Event model is not initialized');
    }

    const { _id, tenant_id } = req.query;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: 'tenant_id and _id are required'
      });
    }

    const event = await Event.findOne({ _id, tenant_id });

    if (!event) {
      return res.status(404).json({
        success: false,
        message: 'Event not found'
      });
    }

    res.status(200).json({
      success: true,
      data: event
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * UPDATE Event (status / severity / raw data)
 ************************************************/
async function update_event(req, res, next) {
  try {
    const Event = req.AnomalyEventModel;
    if (!Event) {
      throw new Error('Event model is not initialized');
    }

    const { _id, tenant_id } = req.body;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: '_id and tenant_id are required for update'
      });
    }

    const updated = await Event.findOneAndUpdate(
      { _id, tenant_id },
      req.body,
      { new: true }
    );

    if (!updated) {
      return res.status(404).json({
        success: false,
        message: 'Event not found'
      });
    }

    res.status(200).json({
      success: true,
      message: 'Event updated successfully',
      data: updated
    });
  } catch (error) {
    next(error);
  }
}

/************************************************
 * DELETE Event (usually avoided in prod, but provided)
 ************************************************/
async function delete_event(req, res, next) {
  try {
    const Event = req.AnomalyEventModel;
    if (!Event) {
      throw new Error('Event model is not initialized');
    }

    const { _id, tenant_id } = req.body;

    if (!_id || !tenant_id) {
      return res.status(400).json({
        success: false,
        message: '_id and tenant_id are required'
      });
    }

    const result = await Event.deleteOne({ _id, tenant_id });

    if (result.deletedCount === 0) {
      return res.status(404).json({
        success: false,
        message: 'Event not found'
      });
    }

    res.status(200).json({
      success: true,
      message: 'Event deleted successfully'
    });
  } catch (error) {
    next(error);
  }
}

module.exports = {
  create_event,
  list_events,
  get_event,
  update_event,
  delete_event
};
