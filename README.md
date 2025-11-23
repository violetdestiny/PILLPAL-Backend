# PillPal — Backend API


![Python](https://img.shields.io/badge/Python-3670A0?style=for-the-badge\&logo=python\&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge\&logo=flask\&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge\&logo=mysql\&logoColor=white)
![Apache](https://img.shields.io/badge/Apache-D22128?style=for-the-badge\&logo=apache\&logoColor=white)
![WSGI](https://img.shields.io/badge/WSGI-444444?style=for-the-badge)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=for-the-badge\&logo=mqtt\&logoColor=white)
![paho-mqtt](https://img.shields.io/badge/paho--mqtt-1E90FF?style=for-the-badge)
![SSL](https://img.shields.io/badge/SSL%20Certbot-3A3A3A?style=for-the-badge\&logo=letsencrypt)



### Related Repositories

| Component                     | Link                                                                                                   |
| ----------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Frontend (Android/Kotlin)** | [https://github.com/f4eriebambi/pillpalMobile](https://github.com/f4eriebambi/pillpalMobile)           |
| **Hardware (Pi Zero)**        | [https://github.com/violetdestiny/PILLPAL-Hardware](https://github.com/violetdestiny/PILLPAL-Hardware) |

---

**Team Pixel Health** 
* Sofia — Backend, Database, Hardware 
* Iker — IoT Hardware, Connectivity 
* Favour — UX/UI Design 
* Ikram — Frontend + Device Integration

#  Overview

The **PillPal Backend** is the cloud backbone of the entire PillPal ecosystem.
It connects:

The **Android mobile app** (login, registration, medications)
 The **IoT pillbox hardware** (via MQTT)
 The **MySQL database** hosted on AWS RDS
 The **secure web server** on AWS EC2 running Apache + WSGI

This backend ensures reliable syncing of:

* Users
* Medication schedules
* Daily reminders
* IoT device events
* Adherence tracking

Everything is encrypted through **HTTPS + SSL certbot**.

---

#  Technologies Used

| Layer                  | Technology                                 |
| ---------------------- | ------------------------------------------ |
| **Web Server**         | Apache2 + WSGI                             |
| **Backend Runtime**    | Python 3                                   |
| **Framework**          | Flask                                      |
| **Database**           | MySQL on Amazon RDS                        |
| **MQTT Messaging**     | Mosquitto broker + Python paho-mqtt client |
| **Auth**               | Token-based (simple token storage)         |
| **Android Networking** | Retrofit, OkHttp                           |
| **Deployment**         | AWS EC2, Route 53, Certbot SSL             |

---

#  What This Backend Does

## **Authentication API**

Endpoints under `/auth/`:

* `/register` — Creates a new user
* `/login` — Returns user + simple session token
* Input validation
* Database storage via parameterized SQL

##  **Medication Management API**

Endpoints under `/medications/`:

* `GET /medications?user_id=X` — Returns all medications + schedule + times
* `POST /medications` — Creates a new medication, schedule rule, and daily times

This is tightly integrated with the MySQL schema:

```
medications
med_schedule_rules
med_times
```

## 3️ **MQTT Device Event Handling**

The backend listens to MQTT messages from the Raspberry Pi:

* `pillpal/device/<device_id>` topics
* Events such as:

  * `pill_taken`
  * `alert_started`
  * telemetries, timestamps, battery, etc.

COMING IN CA3:

* Mapping MQTT → schedule events
* Updating dose_instances

## 4️ **Android App Integration**

The mobile app communicates with:

 `/auth/login`
 `/auth/register`
 `/medications` GET + POST

All through **HTTPS** via `pillpal.space`
The app uses **Retrofit + Gson** to parse backend responses.

---

#  System Architecture



<img width="614" height="509" alt="SysArchitecture" src="https://github.com/user-attachments/assets/4d544017-16ed-4c65-b47c-aada8f05e7a6" />

---

#  MQTT Overview

### MQTT Broker

Running on the Raspberry Pi or cloud instance:

```
mqtt://127.0.0.1:1883
```

### Subscribed Topics

```
pillpal/device/#       # All IoT messages
```

### Example MQTT Event

```json
{
  "device_id": "PILLPAL-001",
  "event": "pill_taken",
  "timestamp": "2025-11-07T08:00:00Z"
}
```

### Mapping Logic (CA3)

| Device Event | Stored As       |
| ------------ | --------------- |
| `pill_taken` | `ack_taken`     |
| default      | `alert_started` |

---

#  Database (AWS RDS MySQL)

<img width="856" height="517" alt="3NF_ERD" src="https://github.com/user-attachments/assets/26ccd93c-d42d-49c0-8d28-d52faf84580b" />

Secure RDS configuration:

* Strong password
* Private network
* SSL enforced
* Parameterized queries
* Automatic backups

---

#  Environment Variables

Create `.env` inside the backend:

```
DB_HOST=< RDS endpoint>
DB_USER=<user>
DB_PASSWORD=<password>
DB_NAME=database

MQTT_BROKER=mqtt://127.0.0.1:1883
```

---

#  Deployment Notes

### Apache + WSGI

The backend runs using `/var/www/pillpal/PILLPAL-Backend`
Inside, Apache loads:

* **WSGI script**
* **Virtual environment**
* **Flask app**

### Domain + SSL

* Domain purchased and configured in **AWS Route 53**
* Certbot installed on EC2
* Automatic HTTPS enforcement
* All API requests encrypted end-to-end

---

#  Test Routes

### Base Route

```
GET https://pillpal.space/api/health
```

Returns:

```json
{ "status": "ok", "db": true }
```

### Fetch Medications

```
GET /api/medications?user_id=1
```

### Create Medication

```
POST /api/medications
```

---

#  Installation

### Install dependencies

```bash
pip install -r requirements.txt
```

### Restart Apache

```bash
sudo systemctl restart apache2
```

---

#  Current Status

This backend currently supports:

✓ User login + registration
✓ Creating medications
✓ Fetching medications
✓ Fully connected MySQL schema
✓ Full Android app integration
✓ Python MQTT client
✓ Apache + WSGI production server
✓ SSL + HTTPS domain

---

# Coming in CA3

* Full MQTT → DB adherence logging
* Device pairing and status tracking
* Complete CRUD for medications
* Full box implementation.
* https://cad.onshape.com/documents/ab0ab6e78c7dc02038fa95e0/w/72d464fa7c6e7aad1d8f76f9/e/c431fd5f781bbfc2fce61794?renderMode=0&uiState=6922f2534c34db92d47210fa
* Notifications + pill reminders
* IoT → App real-time sync
* JWT authentication upgrade
* Security hardening & monitoring

---
