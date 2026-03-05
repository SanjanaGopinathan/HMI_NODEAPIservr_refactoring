const mongoose = require('mongoose');
const connections = {};

/**
 * Connect to MongoDB databases dynamically
 */
async function connectDatabases() {
  try {
    // Read environment variables
    const assetsURI = process.env.MONGO_ASSETS_URI;
    const assetsDB = process.env.MONGO_ASSETS_DB;
    const gatewayURI = process.env.MONGO_GATEWAYS_URI;
    const gatewayDB = process.env.MONGO_GATEWAYS_DB;

    if (!assetsURI || !assetsDB || !gatewayURI || !gatewayDB) {
      throw new Error('MongoDB URI or DB name missing in environment variables');
    }

    // If both URIs and DBs are the same, use a single connection
    if (assetsURI === gatewayURI && assetsDB === gatewayDB) {
      connections.mainDB = mongoose.createConnection(assetsURI, {
        autoIndex: true,
        dbName: assetsDB, // set DB name directly
      });

      connections.assetsDB = connections.mainDB;
      connections.gatewaysDB = connections.mainDB;

      connections.mainDB.on('connected', () =>
        console.log(`Single DB connected: ${assetsDB}`)
      );

    } else {
      // Separate connections for Assets and Gateways
      connections.assetsDB = mongoose.createConnection(assetsURI, {
        autoIndex: true,
        dbName: assetsDB,
      });

      connections.gatewaysDB = mongoose.createConnection(gatewayURI, {
        autoIndex: true,
        dbName: gatewayDB,
      });

      connections.assetsDB.on('connected', () =>
        console.log(`Assets DB connected: ${assetsDB}`)
      );

      connections.gatewaysDB.on('connected', () =>
        console.log(`Gateways DB connected: ${gatewayDB}`)
      );
    }

    // Handle connection errors
    connections.assetsDB?.on('error', (err) =>
      console.error('Assets DB connection error:', err)
    );
    connections.gatewaysDB?.on('error', (err) =>
      console.error('Gateways DB connection error:', err)
    );
    
    // Create indexes for performance
    await createIndexes(connections);

  } catch (error) {
    console.error('MongoDB connection error:', error.message);
    process.exit(1);
  }
}

/**
 * Create indexes on commonly queried fields
 */
async function createIndexes(connections) {
  try {
    console.log('Creating MongoDB indexes...');
    
    // Assets collection indexes
    const assetsDB = connections.assetsDB;
    if (assetsDB) {
      const assetsCollection = assetsDB.collection('assets');
      await assetsCollection.createIndex({ tenant_id: 1 });
      await assetsCollection.createIndex({ tenant_id: 1, site_id: 1 });
      await assetsCollection.createIndex({ tenant_id: 1, site_id: 1, gateway_id: 1 });
      await assetsCollection.createIndex({ status: 1 });
      await assetsCollection.createIndex({ location: 1 });
      console.log('✓ Created indexes on assets collection');
    }
    
    // Gateways collection indexes
    const gatewaysDB = connections.gatewaysDB;
    if (gatewaysDB) {
      const gatewaysCollection = gatewaysDB.collection('gateways');
      await gatewaysCollection.createIndex({ tenant_id: 1 });
      await gatewaysCollection.createIndex({ tenant_id: 1, site_id: 1 });
      console.log('✓ Created indexes on gateways collection');
    }
    
    // If same DB, also create indexes for other collections
    if (assetsDB === gatewaysDB) {
      const policiesCollection = assetsDB.collection('policies');
      await policiesCollection.createIndex({ tenant_id: 1 });
      await policiesCollection.createIndex({ tenant_id: 1, site_id: 1 });
      
      const profilesCollection = assetsDB.collection('profiles');
      await profilesCollection.createIndex({ tenant_id: 1 });
      await profilesCollection.createIndex({ tenant_id: 1, site_id: 1 });
      
      const personnelCollection = assetsDB.collection('personnel');
      await personnelCollection.createIndex({ tenant_id: 1 });
      await personnelCollection.createIndex({ tenant_id: 1, site_id: 1 });
      
      console.log('✓ Created indexes on policies, profiles, and personnel collections');
    }
    
  } catch (error) {
    console.warn('Warning: Could not create all indexes:', error.message);
    // Don't fail startup if indexes can't be created - they might already exist
  }
}

module.exports = {
  connectDatabases,
  connections,
};
