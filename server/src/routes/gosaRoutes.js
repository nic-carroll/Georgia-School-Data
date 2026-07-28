const express = require('express');
const router = express.Router();
const gosaService = require('../services/gosaDataService');

// GET /api/gosa/districts - List all 235 Georgia school districts
router.get('/districts', (req, res) => {
  res.json({
    success: true,
    data: gosaService.getDistricts()
  });
});

// GET /api/gosa/schools - List all 2,301 Georgia public schools
router.get('/schools', (req, res) => {
  res.json({
    success: true,
    data: gosaService.getAllSchools()
  });
});

// GET /api/gosa/schools/search?q=evans - Real-time full-text search across all schools & districts
router.get('/schools/search', (req, res) => {
  const query = req.query.q || '';
  const results = gosaService.searchSchools(query);
  res.json({
    success: true,
    total: results.length,
    data: results
  });
});

// GET /api/gosa/multiyear - 5-Year Historical Performance Trends
router.get('/multiyear', (req, res) => {
  const category = req.query.category || 'act';
  const districtCode = req.query.district || '636';
  const schoolName = req.query.school || 'Evans High School';

  const data = gosaService.getMultiYearTrends(category, districtCode, schoolName);
  res.json({
    success: true,
    data
  });
});

// GET /api/gosa/district/:code/schools - List all schools in a specific district
router.get('/district/:code/schools', (req, res) => {
  const codeOrName = decodeURIComponent(req.params.code);
  const schools = gosaService.getSchoolsByDistrict(codeOrName);
  res.json({
    success: true,
    data: schools
  });
});

// GET /api/gosa/school/:name - Get full GOSA performance metrics for a specific school
router.get('/school/:name', (req, res) => {
  const schoolName = decodeURIComponent(req.params.name);
  const school = gosaService.getSchoolDetails(schoolName);
  res.json({
    success: true,
    data: school
  });
});

// GET /api/gosa/updates/status - Fetch daily update status
router.get('/updates/status', (req, res) => {
  const report = gosaService.getLatestUpdateReport();
  res.json({
    success: true,
    data: report
  });
});

module.exports = router;
