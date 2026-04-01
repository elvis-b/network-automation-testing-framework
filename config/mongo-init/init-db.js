// =============================================================================
// MongoDB Initialization Script
// Network Monitoring System
// =============================================================================
//
// This script runs when MongoDB container starts for the first time.
// It seeds the database with initial data for development/testing.
//
// =============================================================================

// Switch to our database
db = db.getSiblingDB('network_monitoring');

// -----------------------------------------------------------------------------
// Create Users Collection
// -----------------------------------------------------------------------------
print('Creating users collection...');

db.users.insertMany([
    {
        username: "admin",
        password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.V4ferWX.YJq.Gy", // admin123
        email: "admin@example.com",
        role: "admin",
        is_active: true,
        created_at: new Date(),
        last_login: null
    },
    {
        username: "operator",
        password_hash: "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW", // operator123
        email: "operator@example.com",
        role: "operator",
        is_active: true,
        created_at: new Date(),
        last_login: null
    },
    {
        username: "viewer",
        password_hash: "$2b$12$gJp4y4u5SrTq/q2F8Kp8ROZq5p5u5uKdKdKdKdKdKdKdKdKdKdKdK", // viewer123
        email: "viewer@example.com",
        role: "viewer",
        is_active: true,
        created_at: new Date(),
        last_login: null
    }
]);

// Create index on username
db.users.createIndex({ username: 1 }, { unique: true });
print('Users collection created with ' + db.users.countDocuments({}) + ' documents');

// -----------------------------------------------------------------------------
// Create Devices Collection
// -----------------------------------------------------------------------------
print('Creating devices collection...');

db.devices.insertMany([
    {
        name: "core-router-01",
        ip_address: "10.0.0.1",
        device_type: "router",
        vendor: "cisco",
        model: "CSR1000v",
        status: "active",
        location: "Data Center 1",
        created_at: new Date(),
        updated_at: new Date(),
        last_seen: new Date(),
        metadata: {
            os_version: "IOS-XE 17.3",
            serial_number: "9KIBQAQ3OPE",
            uptime: 864000
        }
    },
    {
        name: "core-router-02",
        ip_address: "10.0.0.2",
        device_type: "router",
        vendor: "cisco",
        model: "CSR1000v",
        status: "active",
        location: "Data Center 1",
        created_at: new Date(),
        updated_at: new Date(),
        last_seen: new Date(),
        metadata: {
            os_version: "IOS-XE 17.3",
            serial_number: "9KIBQAQ3OPF",
            uptime: 432000
        }
    },
    {
        name: "dist-switch-01",
        ip_address: "10.0.1.1",
        device_type: "switch",
        vendor: "cisco",
        model: "Catalyst 9300",
        status: "active",
        location: "Building A",
        created_at: new Date(),
        updated_at: new Date(),
        last_seen: new Date(),
        metadata: {
            os_version: "IOS-XE 17.6",
            serial_number: "FCW2214L0VK",
            uptime: 1728000
        }
    },
    {
        name: "dist-switch-02",
        ip_address: "10.0.1.2",
        device_type: "switch",
        vendor: "cisco",
        model: "Catalyst 9300",
        status: "inactive",
        location: "Building B",
        created_at: new Date(),
        updated_at: new Date(),
        last_seen: new Date(),
        metadata: {
            os_version: "IOS-XE 17.6",
            serial_number: "FCW2214L0VL",
            uptime: 0
        }
    },
    {
        name: "edge-firewall-01",
        ip_address: "10.0.2.1",
        device_type: "firewall",
        vendor: "cisco",
        model: "ASA 5525-X",
        status: "active",
        location: "DMZ",
        created_at: new Date(),
        updated_at: new Date(),
        last_seen: new Date(),
        metadata: {
            os_version: "ASA 9.16",
            serial_number: "JMX1950L0NS",
            uptime: 2592000
        }
    }
]);

// Create indexes
db.devices.createIndex({ name: 1 }, { unique: true });
db.devices.createIndex({ ip_address: 1 }, { unique: true });
db.devices.createIndex({ status: 1 });
db.devices.createIndex({ device_type: 1 });
print('Devices collection created with ' + db.devices.countDocuments({}) + ' documents');

// -----------------------------------------------------------------------------
// Create Alerts Collection
// -----------------------------------------------------------------------------
print('Creating alerts collection...');

// Get device IDs for reference
var coreRouter = db.devices.findOne({ name: "core-router-01" });
var distSwitch = db.devices.findOne({ name: "dist-switch-02" });
var firewall = db.devices.findOne({ name: "edge-firewall-01" });

db.alerts.insertMany([
    {
        device_id: coreRouter._id.toString(),
        device_name: "core-router-01",
        severity: "critical",
        type: "performance",
        message: "High CPU utilization detected (95%)",
        timestamp: new Date(),
        acknowledged: false,
        acknowledged_by: null,
        acknowledged_at: null,
        resolved: false,
        resolved_at: null
    },
    {
        device_id: distSwitch._id.toString(),
        device_name: "dist-switch-02",
        severity: "warning",
        type: "connectivity",
        message: "Interface GigabitEthernet0/1 is down",
        timestamp: new Date(),
        acknowledged: false,
        acknowledged_by: null,
        acknowledged_at: null,
        resolved: false,
        resolved_at: null
    },
    {
        device_id: firewall._id.toString(),
        device_name: "edge-firewall-01",
        severity: "info",
        type: "security",
        message: "Configuration backup completed successfully",
        timestamp: new Date(),
        acknowledged: true,
        acknowledged_by: "admin",
        acknowledged_at: new Date(),
        resolved: true,
        resolved_at: new Date()
    }
]);

// Create indexes
db.alerts.createIndex({ device_id: 1 });
db.alerts.createIndex({ severity: 1 });
db.alerts.createIndex({ acknowledged: 1 });
db.alerts.createIndex({ timestamp: -1 });
print('Alerts collection created with ' + db.alerts.countDocuments({}) + ' documents');

// -----------------------------------------------------------------------------
// Summary
// -----------------------------------------------------------------------------
print('');
print('=============================================================================');
print('MongoDB Initialization Complete');
print('=============================================================================');
print('Database: network_monitoring');
print('Collections:');
print('  - users: ' + db.users.countDocuments({}) + ' documents');
print('  - devices: ' + db.devices.countDocuments({}) + ' documents');
print('  - alerts: ' + db.alerts.countDocuments({}) + ' documents');
print('=============================================================================');

