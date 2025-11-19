const express = require('express');
const router = express.Router();

// Temporary routes
router.get('/', (req, res) => {
    res.json({ message: 'Get reminders - to be implemented' });
});

router.post('/', (req, res) => {
    res.json({ message: 'Create reminder - to be implemented' });
});

module.exports = router;