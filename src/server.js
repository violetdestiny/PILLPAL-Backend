const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Basic test route
app.get('/', (req, res) => {
    res.json({ message: 'PillPal Backend API is running!' });
});

// Routes (with error handling for missing files)
try {
    app.use('/api/auth', require('./routes/auth'));
    app.use('/api/medications', require('./routes/medications'));
    app.use('/api/reminders', require('./routes/reminders'));
} catch (error) {
    console.log('Some routes are not implemented yet, but server will still start');
}

// Database connection (optional for now)
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/pillpal';

mongoose.connect(MONGODB_URI, {
    useNewUrlParser: true,
    useUnifiedTopology: true,
})
    .then(() => console.log('Connected to MongoDB'))
    .catch(err => console.log('MongoDB connection error:', err.message));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`✅ Server running on port ${PORT}`);
    console.log(`📍 Test it at: http://localhost:${PORT}`);
});