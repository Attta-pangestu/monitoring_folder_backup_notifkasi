

// Function to generate dummy backup data that mirrors the actual database structure
function generateDummyBackupData() {
  const now = new Date();
  
  // Generate realistic data based on the database context we know
  const statusOptions = ['Success', 'Warning', 'Error'];
  const randomStatus = statusOptions[Math.floor(Math.random() * statusOptions.length)];
  
  // Simulate data similar to staging_PTRJ_iFES_Plantware database
  return {
    timestamp: now.toISOString().replace('T', ' ').substring(0, 19),
    backup_file: `staging_PTRJ_iFES_Plantware_${now.toISOString().replace(/[-:]/g, '').replace('T', '_').substring(0, 15)}.bak`,
    size_mb: Math.floor(Math.random() * 1400) + 100, // Between 100-1500 MB
    tables_count: Math.floor(Math.random() * 30) + 20, // Between 20-50 tables
    gwscandata_records: Math.floor(Math.random() * 9000) + 1000, // Between 1000-10000 records
    ffb_records: Math.floor(Math.random() * 7000) + 1000, // Between 1000-8000 records
    status: randomStatus,
    last_scanned: new Date(now.getTime() - (Math.floor(Math.random() * 23) + 1) * 60 * 60 * 1000)
                  .toISOString().replace('T', ' ').substring(0, 19), // 1-24 hours ago
    database_name: 'staging_PTRJ_iFES_Plantware',
    scanner_users: Math.floor(Math.random() * 100) + 10, // 10-110 scanner users
    fields_monitored: Math.floor(Math.random() * 50) + 5, // 5-55 fields
    vehicle_count: Math.floor(Math.random() * 30) + 5, // 5-35 vehicles
    productivity_score: Math.random() * 100, // 0-100 percentage
    backup_age_hours: Math.floor(Math.random() * 24) // 0-24 hours
  };
}

// Function to validate backup health based on generated data
function validateBackupHealth(backupData) {
  const issues = [];
  
  // Check if backup is too old
  const now = new Date();
  const lastScanned = new Date(backupData.last_scanned);
  const hoursDiff = (now - lastScanned) / (1000 * 60 * 60);
  
  if (hoursDiff > 24) {
    issues.push(`Backup data is ${Math.round(hoursDiff)} hours old (recommended: < 24 hours)`);
  }
  
  // Check unusual file size
  if (backupData.size_mb < 50) {
    issues.push(`Backup file size is unusually small (${backupData.size_mb} MB)`);
  }
  
  // Check record count anomalies
  if (backupData.gwscandata_records < 100 && backupData.status === 'Success') {
    issues.push(`Unusually low GWScanner records (${backupData.gwscandata_records}) for success status`);
  }
  
  if (backupData.ffb_records < 100 && backupData.status === 'Success') {
    issues.push(`Unusually low FFBScanner records (${backupData.ffb_records}) for success status`);
  }
  
  // Check table count
  if (backupData.tables_count < 10) {
    issues.push(`Unusually low table count (${backupData.tables_count})`);
  }
  
  return {
    isHealthy: issues.length === 0,
    issues: issues,
    overallStatus: issues.length > 0 ? 'Warning' : backupData.status
  };
}

module.exports = {
  generateDummyBackupData,
  validateBackupHealth
};