const qrcode = require('qrcode-terminal');
const { Client, LocalAuth } = require('whatsapp-web.js');
const { generateDummyBackupData, validateBackupHealth } = require('./backupService');

// Inisialisasi client dengan session penyimpanan lokal
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: { 
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'] 
    }
});

// Data untuk monitoring backup
let lastBackupCheck = null;
let monitoringInterval = null;

client.on('qr', qr => {
    console.log('Scan the QR code below to connect to WhatsApp:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('Client is ready!');
    console.log('WhatsApp Bot for Database Backup Monitoring is now running...');
    
    // Mulai monitoring backup
    startBackupMonitoring();
});

client.on('authenticated', () => {
    console.log('Authentication successful!');
});

client.on('auth_failure', msg => {
    console.error('Authentication failed:', msg);
});

// Handle incoming messages
client.on('message', async message => {
    // Jangan balas pesan dari diri sendiri
    if (message.fromMe) return;

    const messageBody = message.body.toLowerCase();
    const chat = await message.getChat();

    console.log(`Received message: ${messageBody} from ${chat.name || message.from}`);

    // Respon ke perintah tertentu
    if (messageBody === '!backup' || messageBody === '!status') {
        await sendBackupStatus(message.from);
    } else if (messageBody === '!help') {
        const helpMessage = `*WhatsApp Database Backup Monitor Help* 

Commands:
!backup / !status - Check latest backup status
!health - Check backup health status
!info - Show bot information
!help - Show this help message

This bot monitors database backup status and sends notifications about backup activities.`;
        
        await message.reply(helpMessage);
    } else if (messageBody === '!health') {
        await sendBackupHealth(message.from);
    } else if (messageBody === '!info') {
        const infoMessage = `*Database Backup Monitor Bot*

This bot monitors backup status for systems similar to staging_PTRJ_iFES_Plantware.
- Tracks GW Scanner and FFB Scanner data
- Monitors backup file sizes and record counts
- Validates data freshness
- Sends periodic notifications

Last check: ${lastBackupCheck ? lastBackupCheck.timestamp : 'Never'}`;
        
        await message.reply(infoMessage);
    }
});

// Fungsi untuk mengirim status backup
async function sendBackupStatus(chatId) {
    try {
        if (!lastBackupCheck) {
            await client.sendMessage(chatId, 'No backup data available yet. Please wait for the first check.');
            return;
        }

        const statusEmojis = {
            'Success': '✅',
            'Warning': '⚠️',
            'Error': '❌'
        };

        const statusSymbol = statusEmojis[lastBackupCheck.status] || 'ℹ️';
        
        const message = `*DATABASE BACKUP STATUS REPORT*
${statusSymbol} *Status:* ${lastBackupCheck.status}
📅 *Timestamp:* ${lastBackupCheck.timestamp}
📁 *File:* ${lastBackupCheck.backup_file}
💾 *Size:* ${lastBackupCheck.size_mb} MB
📊 *Tables:* ${lastBackupCheck.tables_count} tables
🔍 *GWScanner Records:* ${lastBackupCheck.gwscandata_records}
📋 *FFBScanner Records:* ${lastBackupCheck.ffb_records}
⏰ *Last Scanned:* ${lastBackupCheck.last_scanned}

${lastBackupCheck.status === 'Success' ? '✅ Backup completed successfully!' : 
  lastBackupCheck.status === 'Warning' ? '⚠️ Backup completed with warnings. Please check backup integrity.' : 
  '❌ Backup failed! Immediate attention required!'}
  
*Additional Info:*
👥 Scanner Users: ${lastBackupCheck.scanner_users}
🌾 Fields Monitored: ${lastBackupCheck.fields_monitored}
🚛 Vehicles: ${lastBackupCheck.vehicle_count}
📈 Productivity: ${lastBackupCheck.productivity_score.toFixed(2)}%
⏳ Backup Age: ${lastBackupCheck.backup_age_hours} hours`;

        await client.sendMessage(chatId, message);
    } catch (error) {
        console.error('Error sending backup status:', error);
        await client.sendMessage(chatId, 'Error retrieving backup status. Please try again later.');
    }
}

// Fungsi untuk mengirim kesehatan backup
async function sendBackupHealth(chatId) {
    try {
        if (!lastBackupCheck) {
            await client.sendMessage(chatId, 'No backup data available yet. Please wait for the first check.');
            return;
        }

        const health = validateBackupHealth(lastBackupCheck);
        
        let healthMessage = `*BACKUP HEALTH REPORT*
🏥 *Overall Status:* ${health.overallStatus}
📊 *Issues Found:* ${health.issues.length}

${health.isHealthy 
    ? '✅ No critical issues found!' 
    : `⚠️ *Issues:* \n${health.issues.map((issue, i) => `${i+1}. ${issue}`).join('\n')}
    
Please address the above issues to maintain backup integrity.`}`;

        await client.sendMessage(chatId, healthMessage);
    } catch (error) {
        console.error('Error sending backup health:', error);
        await client.sendMessage(chatId, 'Error retrieving backup health. Please try again later.');
    }
}

// Fungsi untuk memeriksa status backup
function checkBackupStatus() {
    console.log('Checking backup status...');
    
    // Generate dummy backup data
    const backupData = generateDummyBackupData();
    lastBackupCheck = backupData;
    
    console.log(`Backup status checked: ${backupData.status} - ${backupData.backup_file}`);
    
    // Di sini Anda bisa menambahkan logika untuk menyebarkan notifikasi ke grup/kontak tertentu
    // Saat ini hanya mencetak ke console
    
    return backupData;
}

// Fungsi untuk memulai monitoring backup
function startBackupMonitoring() {
    // Lakukan pengecekan pertama
    checkBackupStatus();
    
    // Atur pengecekan berkala (setiap 10 menit)
    monitoringInterval = setInterval(() => {
        checkBackupStatus();
        
        // Kirim notifikasi ke kontak tertentu (misalnya nomor admin)
        // Anda bisa mengganti ini dengan nomor kontak yang ingin menerima notifikasi
        // broadcastBackupNotification();
    }, 600000); // Setiap 10 menit (600000 ms)
    
    console.log('Backup monitoring started (every 10 minutes)');
}

// Fungsi untuk menyebarkan notifikasi (bisa dikirim ke grup atau kontak khusus)
async function broadcastBackupNotification() {
    if (!lastBackupCheck) return;
    
    try {
        // Di sini Anda bisa menentukan nomor atau grup khusus untuk menerima notifikasi
        // Contoh: kirim ke nomor admin tertentu
        // await client.sendMessage('6281234567890@c.us', 'Backup notification message');
        
        console.log('Backup notification broadcast scheduled');
    } catch (error) {
        console.error('Error broadcasting notification:', error);
    }
}

// Event listener untuk disconnect
client.on('disconnected', (reason) => {
    console.log('Client was logged out', reason);
    if (monitoringInterval) {
        clearInterval(monitoringInterval);
    }
});

client.initialize();