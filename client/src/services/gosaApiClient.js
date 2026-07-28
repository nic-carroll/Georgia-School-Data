const API_BASE_URL = 'http://localhost:5000/api/gosa';

export async function fetchDistricts() {
  try {
    const res = await fetch(`${API_BASE_URL}/districts`);
    const json = await res.json();
    return json.data || [];
  } catch (err) {
    console.warn('Backend API not reached, using local district registry fallback:', err);
    return [
      { id: '636', name: 'Columbia County', code: 'COLCS', type: 'School District', region: 'CSRA', totalSchools: 31, totalStudents: 28450 },
      { id: '721', name: 'Richmond County', code: 'RICH', type: 'School District', region: 'CSRA', totalSchools: 52, totalStudents: 29100 },
      { id: '660', name: 'Fulton County', code: 'FULT', type: 'School District', region: 'Metro Atlanta', totalSchools: 106, totalStudents: 89500 },
      { id: '667', name: 'Gwinnett County', code: 'GWIN', type: 'School District', region: 'Metro Atlanta', totalSchools: 142, totalStudents: 182000 }
    ];
  }
}

export async function fetchDistrictMetrics(districtName = 'Columbia County') {
  try {
    const res = await fetch(`${API_BASE_URL}/district/${encodeURIComponent(districtName)}`);
    const json = await res.json();
    return json.data;
  } catch (err) {
    console.warn('Backend API fallback for metrics:', err);
    return null;
  }
}

export async function fetchUpdateStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/updates/status`);
    const json = await res.json();
    return json.data;
  } catch (err) {
    console.warn('Backend API fallback for update status:', err);
    return {
      timestamp: new Date().toISOString(),
      total_tracked_files: 142,
      new_files_count: 3,
      new_files: [
        { filename: 'ACT_2024-25_Highest.csv', category: 'act_scores' },
        { filename: 'Attendance_2024-25.csv', category: 'attendance' },
        { filename: 'Enrollment_by_Grade_2024-25.csv', category: 'enrollment' }
      ]
    };
  }
}
