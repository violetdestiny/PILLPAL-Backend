const express = require('express');
const cors = require('cors');
const mysql = require('mysql2');
const mqtt = require('mqtt');
require('dotenv').config();

const app = express();

// -------------------------------------------------------
// Middleware
app.use(cors());
app.use(express.json());

// -------------------------------------------------------
// Basic test route
app.get('/', (req, res) => {
  res.json({ message: 'PillPal Backend API is running!' });
});

// -------------------------------------------------------
// Database Connection
const db = mysql.createConnection({
  host: process.env.MYSQL_HOST,
  user: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE,
  port: process.env.MYSQL_PORT || 3306,
});

db.connect((err) => {
  if (err) {
    console.error('MySQL connection error:', err.message);
  } else {
    console.log('Connected to MySQL database!');
  }
});

// -------------------------------------------------------
// MQTT Integration → dose_events
const MQTT_BROKER = process.env.MQTT_BROKER || 'mqtt://127.0.0.1:1883';
const MQTT_TOPIC = 'pillpal/device/#';

const mqttClient = mqtt.connect(MQTT_BROKER);

mqttClient.on('connect', () => {
  console.log(`📡 Connected to MQTT broker at ${MQTT_BROKER}`);
  mqttClient.subscribe(MQTT_TOPIC, (err) => {
    if (!err) console.log(`Subscribed to ${MQTT_TOPIC}`);
    else console.error('MQTT subscription error:', err.message);
  });
});

mqttClient.on('message', (topic, message) => {
  try {
    const payload = JSON.parse(message.toString());
    console.log('Event received:', payload);

    // Map MQTT event to DB event_type
    const eventType = payload.event === 'pill_taken' ? 'ack_taken' : 'alert_started';

    // Find the device by nickname or hw_model
    const findDeviceQuery = `
      SELECT device_id FROM devices 
      WHERE nickname = ? OR hw_model = ? 
      LIMIT 1
    `;
    db.query(findDeviceQuery, [payload.device_id, payload.device_id], (err, rows) => {
      if (err) return console.error('DB device lookup error:', err.message);

      if (rows.length === 0) {
        console.warn('Unknown device ID:', payload.device_id);
        return;
      }

      const deviceId = rows[0].device_id;

      // Find latest dose instance for that device’s user
      const findInstance = `
        SELECT di.instance_id 
        FROM dose_instances di
        JOIN medications m ON di.med_id = m.med_id
        JOIN device_pairings dp ON dp.user_id = m.user_id
        WHERE dp.device_id = ? 
        ORDER BY di.scheduled_at DESC 
        LIMIT 1;
      `;

      db.query(findInstance, [deviceId], (err, results) => {
        if (err) return console.error('Instance lookup error:', err.message);
        if (results.length === 0) {
          console.warn('No matching dose instance found for device', deviceId);
          return;
        }

        const instanceId = results[0].instance_id;
        const insertEvent = `
          INSERT INTO dose_events (instance_id, event_type, source, meta, created_at)
          VALUES (?, ?, 'device', ?, ?)
        `;
        const meta = JSON.stringify(payload);
        db.query(insertEvent, [instanceId, eventType, meta, payload.timestamp], (err) => {
          if (err) console.error('Failed to insert dose_event:', err.message);
          else console.log('dose_event recorded for instance', instanceId);
        });

        // update dose_instances status
        if (eventType === 'ack_taken') {
          db.query(
            `UPDATE dose_instances SET status = 'taken' WHERE instance_id = ?`,
            [instanceId],
            (err) => {
              if (err) console.error('Failed to update dose_instance:', err.message);
            }
          );
        }
      });
    });
  } catch (err) {
    console.error('⚠️ MQTT message error:', err.message);
  }
});

// -------------------------------------------------------
// Routes (safe import for existing modules)
try {
  app.use('/api/auth', require('./routes/auth'));
  app.use('/api/medications', require('./routes/medications'));
  app.use('/api/reminders', require('./routes/reminders'));
} catch {
  console.log('⚠️ Some route files not implemented yet, but server will still start.');
}

// -------------------------------------------------------
// Start Server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📍 Test it at: http://localhost:${PORT}`);
});
