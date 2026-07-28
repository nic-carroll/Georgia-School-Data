import React, { useState, useEffect } from 'react';
import { useBrand } from '../brands/BrandProvider';
import { fetchDistricts, fetchDistrictMetrics, fetchUpdateStatus } from '../services/gosaApiClient';
import '../styles/dashboard.css';

export function GosaDashboard() {
  const { activeBrand, brandId, setBrand, availableBrands } = useBrand();
  
  const [districts, setDistricts] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('Columbia County');
  const [districtData, setDistrictData] = useState(null);
  const [updateReport, setUpdateReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadInitialData() {
      setLoading(true);
      const districtList = await fetchDistricts();
      setDistricts(districtList);

      const status = await fetchUpdateStatus();
      setUpdateReport(status);

      const metrics = await fetchDistrictMetrics(selectedDistrict);
      setDistrictData(metrics);
      setLoading(false);
    }
    loadInitialData();
  }, []);

  const handleDistrictChange = async (e) => {
    const newDistrict = e.target.value;
    setSelectedDistrict(newDistrict);
    setLoading(true);
    const metrics = await fetchDistrictMetrics(newDistrict);
    setDistrictData(metrics);
    setLoading(false);
  };

  const handleBrandChange = (e) => {
    setBrand(e.target.value);
  };

  if (loading || !districtData) {
    return (
      <div className="gosa-dashboard" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ color: 'var(--brand-primary)' }}>Loading GOSA Educational Analytics...</h2>
          <p>Processing Georgia state report card datasets</p>
        </div>
      </div>
    );
  }

  const { metrics, history, milestonesBySubject } = districtData;

  return (
    <div className="gosa-dashboard">
      {/* Brand & App Top Navigation Header */}
      <header className="dashboard-header">
        <div className="brand-identity">
          {activeBrand.logoUrl && (
            <img src={activeBrand.logoUrl} alt={activeBrand.name} className="brand-logo-img" />
          )}
          <div className="brand-titles">
            <h1>{activeBrand.name} Analytics</h1>
            <p>Georgia Governor's Office of Student Achievement (GOSA) Dashboard</p>
          </div>
        </div>

        <div className="brand-selector-control">
          <span>Brand Theme:</span>
          <select value={brandId} onChange={handleBrandChange}>
            {Object.values(availableBrands).map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>
        </div>
      </header>

      <div className="dashboard-container">
        {/* Daily Update Alert Notification Banner */}
        {updateReport && (
          <div className="update-alert-banner">
            <div>
              <span className="alert-badge">Daily Auto-Ingestion Active</span>
              <strong>GOSA Data Synced Today ({new Date(updateReport.timestamp).toLocaleDateString()})</strong>
              <p>
                Tracked <strong>{updateReport.total_tracked_files}</strong> state files. Identified and auto-ingested{' '}
                <strong>{updateReport.new_files_count}</strong> new datasets.
              </p>
            </div>
            <div style={{ fontSize: '0.8rem', opacity: 0.8 }}>
              Source: goews.georgia.gov
            </div>
          </div>
        )}

        {/* District & Filter Control Bar */}
        <div className="controls-bar">
          <div className="control-group">
            <label>School District / System</label>
            <select value={selectedDistrict} onChange={handleDistrictChange}>
              {districts.map((d) => (
                <option key={d.id} value={d.name}>
                  {d.name} {d.code !== 'STATE' ? `(${d.code})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>School Year</label>
            <select defaultValue="2024-2025">
              <option value="2024-2025">2024-2025 (Latest Released)</option>
              <option value="2023-2024">2023-2024</option>
              <option value="2022-2023">2022-2023</option>
              <option value="2021-2022">2021-2022</option>
            </select>
          </div>
        </div>

        {/* Key Performance Metrics (KPI Cards) */}
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-title">Graduation Rate (Cohort)</div>
            <div className="kpi-value">{metrics.graduationRate}%</div>
            <div className="badge-comparison">
              +{(metrics.graduationRate - metrics.stateGraduationRate).toFixed(1)}% vs State Avg ({metrics.stateGraduationRate}%)
            </div>
            <div className="kpi-subtext">Source: GOSA High School Outcomes</div>
          </div>

          <div className="kpi-card accent-border">
            <div className="kpi-title">GA Milestones Proficiency</div>
            <div className="kpi-value">{metrics.milestonesProficient}%</div>
            <div className="badge-comparison">
              +{(metrics.milestonesProficient - metrics.stateMilestonesProficient).toFixed(1)}% vs State Avg ({metrics.stateMilestonesProficient}%)
            </div>
            <div className="kpi-subtext">Proficient &amp; Distinguished Learners</div>
          </div>

          <div className="kpi-card">
            <div className="kpi-title">Student Attendance Rate</div>
            <div className="kpi-value">{metrics.attendanceRate}%</div>
            <div className="kpi-subtext">Students absent ≤ 5 days per school year</div>
          </div>

          <div className="kpi-card accent-border">
            <div className="kpi-title">Financial Efficiency Rating</div>
            <div className="kpi-value">{metrics.financialEfficiencyStars} / 5.0 ★</div>
            <div className="kpi-subtext">Per Pupil Expenditure: ${metrics.perPupilExpenditure.toLocaleString()}</div>
          </div>
        </div>

        {/* Charts & Breakdown Grid */}
        <div className="data-sections-grid">
          {/* Georgia Milestones Subject Breakdown */}
          <div className="section-card">
            <h2>
              <span>Georgia Milestones Assessment Performance</span>
              <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: 'var(--brand-text-secondary)' }}>
                District vs State Proficiency
              </span>
            </h2>

            <div className="progress-list">
              {milestonesBySubject.map((item, idx) => (
                <div key={idx} className="progress-item">
                  <div className="progress-label">
                    <span>{item.subject}</span>
                    <span style={{ color: 'var(--brand-primary)' }}>{item.proficientPct}% Proficient</span>
                  </div>
                  <div className="bar-container">
                    <div className="bar-fill" style={{ width: `${item.proficientPct}%` }}></div>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--brand-text-secondary)' }}>
                    State Average: {item.stateAvgPct}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Historical Trend & Quick District Info */}
          <div className="section-card">
            <h2>
              <span>5-Year District Trends</span>
            </h2>
            <div className="progress-list">
              {history.map((h, i) => (
                <div key={i} style={{ padding: '0.6rem 0', borderBottom: i < history.length - 1 ? '1px solid #E2E8F0' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', fontSize: '0.9rem' }}>
                    <span>{h.year}</span>
                    <span style={{ color: 'var(--brand-primary)' }}>Grad: {h.gradRate}%</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--brand-text-secondary)', marginTop: '0.2rem' }}>
                    Milestones: {h.milestonesProficient}% | Attendance: {h.attendance}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
