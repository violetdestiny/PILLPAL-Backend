const express = require('express');
const router = express.Router();

// Temporary routes
router.get('/', (req, res) => {
    res.json({ message: 'Get medications - to be implemented' });
});

router.post('/', (req, res) => {
    res.json({ message: 'Add medication - to be implemented' });
});

module.exports = router;