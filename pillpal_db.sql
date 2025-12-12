/* PILLPAL DATABASE */

DROP DATABASE IF EXISTS pillpal_db;
CREATE DATABASE pillpal_db;
USE pillpal_db;

/* USERS */
CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  full_name VARCHAR(100),
  birthday DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_profiles (
  profile_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  full_name VARCHAR(100),
  username VARCHAR(100) UNIQUE,
  timezone VARCHAR(50) DEFAULT 'UTC',
  birth_date DATE,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

/* DEVICES */
CREATE TABLE devices (
  device_id INT AUTO_INCREMENT PRIMARY KEY,
  hw_model VARCHAR(100) NOT NULL,
  fw_version VARCHAR(20) DEFAULT '0.1',
  nickname VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE device_pairings (
  pairing_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  device_id INT NOT NULL,
  active BOOLEAN DEFAULT TRUE,
  paired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  unpaired_at TIMESTAMP NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

/* COMPARTMENTS */
CREATE TABLE compartments (
  compartment_id INT AUTO_INCREMENT PRIMARY KEY,
  device_id INT NOT NULL,
  slot_number INT NOT NULL,
  label VARCHAR(100),
  UNIQUE (device_id, slot_number),
  FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

/* MEDICATIONS */
CREATE TABLE medications (
  med_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  name VARCHAR(100) NOT NULL,
  notes TEXT,
  start_date DATE NOT NULL,
  end_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

/* COMPARTMENT ASSIGNMENTS */
CREATE TABLE compartment_assignments (
  assignment_id INT AUTO_INCREMENT PRIMARY KEY,
  med_id INT NOT NULL,
  compartment_id INT NOT NULL,
  assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  removed_at TIMESTAMP NULL,
  FOREIGN KEY (med_id) REFERENCES medications(med_id) ON DELETE CASCADE,
  FOREIGN KEY (compartment_id) REFERENCES compartments(compartment_id) ON DELETE CASCADE
);

/* SCHEDULE RULES */
CREATE TABLE med_schedule_rules (
  rule_id INT AUTO_INCREMENT PRIMARY KEY,
  med_id INT NOT NULL,
  repeat_type ENUM('daily','weekly','custom') NOT NULL,
  day_mask CHAR(7) NOT NULL DEFAULT '1111111',
  lead_minutes INT NOT NULL DEFAULT 0,
  FOREIGN KEY (med_id) REFERENCES medications(med_id) ON DELETE CASCADE
);

CREATE TABLE med_times (
  time_id INT AUTO_INCREMENT PRIMARY KEY,
  rule_id INT NOT NULL,
  hhmm TIME NOT NULL,
  sort_order SMALLINT NOT NULL DEFAULT 1,
  UNIQUE (rule_id, hhmm),
  FOREIGN KEY (rule_id) REFERENCES med_schedule_rules(rule_id) ON DELETE CASCADE
);

/* DOSES + EVENTS */
CREATE TABLE dose_instances (
  instance_id INT AUTO_INCREMENT PRIMARY KEY,
  med_id INT NOT NULL,
  scheduled_at DATETIME NOT NULL,
  status ENUM('scheduled','taken','snoozed','missed','cancelled') NOT NULL DEFAULT 'scheduled',
  created_source ENUM('app','device') NOT NULL DEFAULT 'app',
  UNIQUE (med_id, scheduled_at),
  FOREIGN KEY (med_id) REFERENCES medications(med_id) ON DELETE CASCADE
);

CREATE TABLE dose_events (
  event_id INT AUTO_INCREMENT PRIMARY KEY,
  instance_id INT NOT NULL,
  event_type ENUM('alert_started','ack_taken','snooze','miss','cancel') NOT NULL,
  source ENUM('device','app') NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  meta TEXT,
  FOREIGN KEY (instance_id) REFERENCES dose_instances(instance_id) ON DELETE CASCADE
);

/* SETTINGS & STATE */
CREATE TABLE notification_settings (
  setting_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  sound_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  vibration_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  led_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  lead_minutes_default INT NOT NULL DEFAULT 5,
  dyslexia_font BOOLEAN NOT NULL DEFAULT FALSE,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE device_state (
  state_id INT AUTO_INCREMENT PRIMARY KEY,
  device_id INT NOT NULL,
  battery_percent SMALLINT,
  last_sync_at TIMESTAMP NULL,
  FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

/* SEED DATA */

INSERT INTO users (email, password_hash, full_name, birthday)
VALUES
  ('maggie@example.com', '$2b$12$examplehashmaggie..............', 'Margaret Lewis', '1953-05-14'),
  ('maria@example.com', '$2b$12$examplehashmaria..............', 'Maria Hernandez', '1998-01-09');

INSERT INTO user_profiles (user_id, full_name, username, timezone, birth_date)
VALUES
  (1, 'Margaret Lewis', 'maggie', 'Europe/Dublin', '1953-05-14'),
  (2, 'Maria Hernandez', 'maria', 'Europe/Dublin', '1998-01-09');

INSERT INTO devices (hw_model, fw_version, nickname)
VALUES ('Pi Zero + PillPal', '0.1', 'Pillbox-01');

INSERT INTO device_pairings (user_id, device_id, active)
VALUES (1, 1, TRUE);

INSERT INTO compartments (device_id, slot_number, label)
VALUES
  (1,1,'Morning A'),
  (1,2,'Morning B'),
  (1,3,'Noon'),
  (1,4,'Afternoon'),
  (1,5,'Evening A'),
  (1,6,'Evening B');

INSERT INTO medications (user_id, name, notes, start_date, end_date)
VALUES
  (1, 'Lisinopril', 'BP medication. Take with water.', '2025-10-15', NULL);

INSERT INTO compartment_assignments (med_id, compartment_id)
VALUES (1,1);

INSERT INTO med_schedule_rules (med_id, repeat_type, day_mask, lead_minutes)
VALUES (1, 'daily', '1111111', 5);

INSERT INTO med_times (rule_id, hhmm, sort_order)
VALUES
  (1, '08:00:00', 1),
  (1, '20:00:00', 2);

INSERT IGNORE INTO dose_instances (med_id, scheduled_at, status, created_source)
VALUES
  (1, '2025-10-25 08:00:00', 'taken', 'device'),
  (1, '2025-10-25 20:00:00', 'missed', 'device'),
  (1, '2025-10-26 08:00:00', 'taken', 'device'),
  (1, '2025-10-26 20:00:00', 'scheduled', 'app');

INSERT INTO dose_events (instance_id, event_type, source, meta)
VALUES
  (1, 'ack_taken', 'device', '{"note":"auto confirm yesterday AM"}'),
  (3, 'ack_taken', 'device', '{"note":"confirm today AM"}');

INSERT INTO notification_settings (user_id)
VALUES (1), (2);

INSERT INTO device_state (device_id, battery_percent, last_sync_at)
VALUES (1, 77, NOW());
