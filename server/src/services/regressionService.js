const fs = require('fs');
const path = require('path');

const REGRESSION_FILE = path.join(__dirname, '..', '..', 'data', 'gosa', 'regression_results.json');

class RegressionService {
  getRegressionData(subjectId = 'g3_ela') {
    if (fs.existsSync(REGRESSION_FILE)) {
      try {
        const raw = fs.readFileSync(REGRESSION_FILE, 'utf-8');
        const json = JSON.parse(raw);
        return json.results[subjectId] || json.results['g3_ela'];
      } catch (err) {
        console.error('Error reading regression_results.json:', err);
      }
    }
    return null;
  }

  getLikeSchools(schoolName, margin = 10.0, subjectId = 'g3_ela') {
    const regData = this.getRegressionData(subjectId);
    if (!regData) return [];

    const targetSchool = regData.dataPoints.find(
      (s) => s.schoolName.toLowerCase() === schoolName.toLowerCase()
    );

    if (!targetSchool) return regData.dataPoints.slice(0, 5);

    const targetEco = targetSchool.ecoDisadvPct;

    // Filter schools within +/- margin percentage of economically disadvantaged rate
    const peerGroup = regData.dataPoints.filter(
      (s) => Math.abs(s.ecoDisadvPct - targetEco) <= margin
    );

    return {
      targetSchool,
      peerGroup: peerGroup.sort((a, b) => b.residual - a.residual)
    };
  }
}

module.exports = new RegressionService();
