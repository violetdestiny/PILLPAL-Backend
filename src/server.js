const express = require('express');
const cors = require('cors');
const mysql = require('mysql2');
require('dotenv').config();
console.log("Loaded ENV:");
console.log("MYSQL_HOST:", process.env.MYSQL_HOST);
console.log("MYSQL_PORT:", process.env.MYSQL_PORT);



const app = express();

//----------- Middleware
app.use(cors());
app.use(express.json());

//--------- Basic test route
app.get('/', (req, res) => {
  res.json({ message: 'PillPal Backend API is running!' });
});

//----------- DB Connection (MySQL via mysql2)
const db = mysql.createConnection({
  host: process.env.MYSQL_HOST,
  user: process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE,
  port: process.env.MYSQL_PORT || 3306
});


db.connect(err => {
  if (err) {
    console.error('❌ MySQL connection error:', err.message);
  } else {
    console.log('✅ Connected to MySQL database!');
  }
});

// -------------------------------------------------------
// Routes (import safely even if some missing)
// -------------------------------------------------------
try {
  app.use('/api/auth', require('./routes/auth'));
  app.use('/api/medications', require('./routes/medications'));
  app.use('/api/reminders', require('./routes/reminders'));
} catch (error) {
  console.log('⚠️ Some route files not implemented yet, but server will still start.');
}

// -------------------------------------------------------
// Example API Endpoints for Testing Database
// -------------------------------------------------------

// Get all users
app.get('/api/users', (req, res) => {
  db.query('SELECT * FROM users', (err, results) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(results);
  });
});

// Add a new user
app.post('/api/users', (req, res) => {
  const { email, password_hash } = req.body;
  if (!email || !password_hash) {
    return res.status(400).json({ error: 'Email and password_hash are required' });
  }

  db.query(
    'INSERT INTO users (email, password_hash) VALUES (?, ?)',
    [email, password_hash],
    (err, result) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'User added successfully', id: result.insertId });
    }
  );
});

// -------------------------------------------------------
// Start Server
// -------------------------------------------------------
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📍 Test it at: http://localhost:${PORT}`);
});
