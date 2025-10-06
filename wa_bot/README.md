# WhatsApp Database Backup Monitor

A WhatsApp bot that monitors database backup status and sends notifications via WhatsApp. This bot is designed to monitor the status of database backups, particularly for systems similar to staging_PTRJ_iFES_Plantware database.

## Features

- Monitors database backup status
- Sends WhatsApp notifications with backup status
- Generates realistic dummy data based on actual database structure
- Periodic monitoring with configurable intervals
- Health validation for backup data
- Web interface to check status and trigger manual checks

## Database Context

This bot is designed with knowledge of these database structures:
- **staging_PTRJ_iFES_Plantware**: Contains tables like Gwscannerdata, Ffbscannerdata, Scanner_User, Field_Profile
- Monitors records for GW Scanner and FFB Scanner activities
- Tracks backup file sizes, record counts, and table counts
- Validates data freshness and integrity

## Prerequisites

- Node.js (v14 or higher)
- npm (v6 or higher)

## Setup

1. Clone the repository
   ```bash
   git clone <your-repo-url>
   cd wa_bot
   ```

2. Install dependencies
   ```bash
   npm install
   ```

3. Create a `.env` file with your configuration:
   ```env
   # WhatsApp API Configuration
   WHATSAPP_API_URL=https://api.whatsapp.com
   WHATSAPP_PHONE_NUMBER=6281234567890

   # If using Twilio
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_WHATSAPP_NUMBER=your_twilio_whatsapp_number

   # If using other provider
   WHATSAPP_API_KEY=your_api_key

   # Database Backup Monitoring Configuration
   BACKUP_MONITORING_INTERVAL=30000  # Interval in milliseconds (30 seconds default)
   BACKUP_PATH=./backups
   PORT=3000
   ```

4. Start the server
   ```bash
   npm start
   ```

## Usage

- Visit `http://localhost:3000` to access the web interface
- Click "Check Backup Now" to trigger an immediate backup status check
- The bot will automatically check backup status periodically based on `BACKUP_MONITORING_INTERVAL`
- Check logs for sent WhatsApp messages (in dummy mode, messages will be logged to console)

## API Endpoints

- `GET /` - Web interface
- `POST /check` - Trigger immediate backup status check
- `GET /status` - Get current monitoring status

## Configuration

- `BACKUP_MONITORING_INTERVAL` - How often to check backup status (in milliseconds)
- `WHATSAPP_PHONE_NUMBER` - The phone number to send notifications to
- Other API-specific configurations based on your chosen WhatsApp API provider

## WhatsApp API Integration

This bot is designed to work with various WhatsApp API providers:

1. **Twilio**: Uncomment the Twilio implementation in `whatsappService.js` and configure your Twilio credentials
2. **WhatsApp Business API**: Use the generic API implementation
3. **Other providers**: Modify `whatsappService.js` to match your provider's API

## Dummy Mode

By default, the bot runs in dummy mode - it simulates sending WhatsApp messages and logs them to the console. To use real WhatsApp API:

1. Configure your WhatsApp API credentials in `.env`
2. Update `whatsappService.js` to use your chosen API provider

## Data Structure

The bot generates realistic backup data including:
- Backup file names and sizes
- Record counts for different tables
- Status tracking (Success, Warning, Error)
- Timestamps for data freshness validation

## License

MIT