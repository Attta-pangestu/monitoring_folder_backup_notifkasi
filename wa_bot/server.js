const express = require('express');
const axios = require('axios');
const dotenv = require('dotenv');
const { generateDummyBackupData } = require('./backupService');
const { sendWhatsAppMessage } = require('./whatsappService');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static('public'));

// Simulated backup monitoring
let lastBackupCheck = null;

// Function to simulate backup check
async function checkBackupStatus() {
  console.log('Checking backup status...');
  
  // Generate dummy backup data that mimics the database structure
  const backupData = generateDummyBackupData();
  
  // Prepare message
  const message = `DATABASE BACKUP STATUS REPORT
==============================
Status: ${backupData.status}
Timestamp: ${backupData.timestamp}
File: ${backupData.backup_file}
Size: ${backupData.size_mb} MB
Tables: ${backupData.tables_count} tables
GWScanner Records: ${backupData.gwscandata_records}
FFBScanner Records: ${backupData.ffb_records}
Last Scanned: ${backupData.last_scanned}

${backupData.status === 'Success' ? '✅ Backup completed successfully!' : 
  backupData.status === 'Warning' ? '⚠️ Backup completed with warnings. Please check backup integrity.' : 
  '❌ Backup failed! Immediate attention required!'}
  `;
  
  // Send WhatsApp notification (in dummy mode, just log it)
  try {
    const result = await sendWhatsAppMessage(message, process.env.WHATSAPP_PHONE_NUMBER);
    console.log('WhatsApp message sent:', result);
  } catch (error) {
    console.error('Error sending WhatsApp message:', error.message);
  }
  
  lastBackupCheck = backupData;
  return backupData;
}

// Routes
app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>WhatsApp Backup Monitor</title></head>
      <body>
        <h1>WhatsApp Database Backup Monitor</h1>
        <p>Status: Running</p>
        <button onclick="checkNow()">Check Backup Now</button>
        <div id="result"></div>
        <script>
          async function checkNow() {
            const response = await fetch('/check', { method: 'POST' });
            const data = await response.json();
            document.getElementById('result').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
          }
        </script>
      </body>
    </html>
  `);
});

app.post('/check', async (req, res) => {
  try {
    const result = await checkBackupStatus();
    res.json({ success: true, data: result });
  } catch (error) {
    console.error('Error in /check endpoint:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/status', (req, res) => {
  res.json({ 
    status: 'running', 
    lastCheck: lastBackupCheck,
    timestamp: new Date().toISOString()
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
  
  // Initial check
  checkBackupStatus();
  
  // Set up periodic checks
  setInterval(checkBackupStatus, process.env.BACKUP_MONITORING_INTERVAL || 30000);
});

module.exports = app;