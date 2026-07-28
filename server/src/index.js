const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const gosaRoutes = require('./routes/gosaRoutes');

const app = express();
const PORT = process.env.PORT || 5000;
const ALLOWED_ORIGIN = process.env.CLIENT_ORIGIN || 'http://localhost:5173';

app.use(helmet());
app.use(cors({ origin: ALLOWED_ORIGIN }));
app.use(express.json());

// API Routes
app.use('/api/gosa', gosaRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`GOSA Data API Server listening on http://localhost:${PORT}`);
});
