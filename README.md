# PillPal — Backend API

![Express](https://img.shields.io/badge/Express.js-000000?style=for-the-badge&logo=express&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge&logo=mqtt&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![dotenv](https://img.shields.io/badge/dotenv-ECD53F?style=for-the-badge&logo=dotenv&logoColor=black)
![CORS](https://img.shields.io/badge/CORS-FF8800?style=for-the-badge)
![bcryptjs](https://img.shields.io/badge/bcryptjs-0086FF?style=for-the-badge)
![nodemon](https://img.shields.io/badge/nodemon-76D04B?style=for-the-badge&logo=nodemon&logoColor=white)


| Component                        | Link                                                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Frontend (Android/Kotlin)** | [https://github.com/violetdestiny/PILLPAL-Frontend](https://github.com/f4eriebambi/pillpalMobile) |
| **Hardware (Pi Zero)**        | [https://github.com/violetdestiny/PILLPAL-Hardware](https://github.com/violetdestiny/PILLPAL-Hardware) |

---

## Contributors

**Team Pixel Health**

* Sofia — Backend, Database, Hardware
* Iker — IoT Hardware, Connectivity
* Favour — UX/UI Design
* Ikram — Frontend + Device Integration

---

The **PillPal Backend** is the central system that connects the PillPal **mobile app**, **IoT pillbox hardware**, and **cloud database**.
It provides REST API endpoints for the app, listens to **MQTT events** from the device, and stores all medication schedules and adherence history in MySQL.

This backend ensures the entire PillPal ecosystem syncs reliably, even when the hardware or app goes offline.

---

##  Technologies & Stack

| Component                | Tech                     |
| ------------------------ | ------------------------ |
| **Runtime**              | Node.js (Express)        |
| **Database**             | MySQL (mysql2 driver)    |
| **Messaging**            | MQTT (Mosquitto broker)  |
| **Auth**                 | JWT (via `/auth` routes) |
| **Environment**          | dotenv                   |
| **Cross-Origin Support** | CORS middleware          |

---

## What This Backend Does

###  **1. Provides REST API for the mobile app**

* User authentication
* CRUD for medications
* Scheduling endpoints
* Retrieve dose history
* Device pairing

### **2. Listens to MQTT events from the pillbox**

* `alert_started`
* `pill_taken` (mapped -> `ack_taken`)
* Any additional device telemetry (battery, lid state, etc.)

And writes them into:

* `dose_events`
* `dose_instances`

### **3. Links devices → users → scheduled medication**

Using the ERD logic:

```
device -> device_pairings -> user -> medications -> dose_instances -> dose_events
```

### **4. Maintains accurate adherence logs**

* Updates dose instance status automatically
* Stores full event metadata (timestamps, raw JSON)

---

## System Architecture

<img width="1493" height="890" alt="Screenshot 2025-11-23 234614" src="https://github.com/user-attachments/assets/6e9c734c-e0d3-4844-934e-40f809fead64" />

---

## MQTT Event Handling

### MQTT Broker

Defined in  `.env`:

```
MQTT_BROKER=mqtt://127.0.0.1:1883
```

### Subscribed Topics

```
pillpal/device/#
```

### Example incoming payload

```json
{
  "device_id": "PILLPAL-001",
  "event": "pill_taken",
  "timestamp": "2025-11-07T08:00:00Z"
}
```

### Event Mapping Logic

| Device Event | Mapped Database event_type |
| ------------ | -------------------------- |
| `pill_taken` | `ack_taken`                |
| (default)    | `alert_started`            |

Events update:

* `dose_events`
* `dose_instances.status`

---

## Database Integration

The backend connects using:
<img width="856" height="517" alt="3NF_ERD" src="https://github.com/user-attachments/assets/26ccd93c-d42d-49c0-8d28-d52faf84580b" />

```js
mysql.createConnection({
  host: process.env.MYSQL_HOST,
  user: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE
})
```

If the device publishes an event, the backend:

1. Finds the correct device
2. Finds the latest dose instance tied to the user
3. Inserts a row into `dose_events`
4. Updates the dose instance status

---

## Environment Variables

Create an `.env` file in the backend folder:

```
# MySQL
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DATABASE=pillpal
MYSQL_PORT=3306

# MQTT
MQTT_BROKER=mqtt://127.0.0.1:1883

# Server
PORT=5000
JWT_SECRET=supersecret
```

---

## Installation & Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure `.env`

See environment variable section above.

### 3. Start the backend

```bash
npm start
```

### 4. Test the server

Visit:

```
http://localhost:5000/
```

---

## Test Routes (Base)

```
GET /
Response: { "message": "PillPal Backend API is running!" }
```
