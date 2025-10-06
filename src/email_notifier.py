import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser
import os
from datetime import datetime

class EmailNotifier:
    def __init__(self, config_file='config/config.ini'):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
        self.config.read(self.config_path)

        self.sender_email = self.config['EMAIL']['sender_email']
        self.sender_password = self.config['EMAIL']['sender_password']
        self.receiver_email = self.config['EMAIL']['receiver_email']
        self.smtp_server = self.config['EMAIL']['smtp_server']
        self.smtp_port = int(self.config['EMAIL']['smtp_port'])
        self.default_subject = self.config['NOTIFICATION']['subject']

    def send_notification(self, subject=None, message="", attachment_path=None):
        """
        Kirim email notifikasi
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = subject or self.default_subject

            # Add body
            body = f"""
            <html>
            <body>
                <h2>Database Backup Monitoring Report</h2>
                <p><strong>Waktu:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                {message}
                <hr>
                <p><em>Email ini dikirim secara otomatis oleh sistem monitoring database backup</em></p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            # Connect to SMTP server and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.ehlo()  # Extended Hello
            server.login(self.sender_email, self.sender_password)

            text = msg.as_string()
            server.sendmail(self.sender_email, self.receiver_email, text)
            server.quit()

            return True, "Email berhasil dikirim"

        except Exception as e:
            return False, f"Gagal mengirim email: {str(e)}"

    def send_backup_report(self, backup_info):
        """
        Kirim laporan backup
        backup_info: dict containing backup information
        """
        message = f"""
        <h3>Informasi Backup Database</h3>
        <table border="1" style="border-collapse: collapse;">
            <tr>
                <td><strong>Nama File:</strong></td>
                <td>{backup_info.get('filename', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Ukuran File:</strong></td>
                <td>{backup_info.get('size', 'N/A')} MB</td>
            </tr>
            <tr>
                <td><strong>Tanggal Backup:</strong></td>
                <td>{backup_info.get('backup_date', 'N/A')}</td>
            </tr>
            <tr>
                <td><strong>Status:</strong></td>
                <td>{backup_info.get('status', 'N/A')}</td>
            </tr>
        </table>

        <h3>Query Results</h3>
        <table border="1" style="border-collapse: collapse;">
        """

        # Add query results
        for table_name, result in backup_info.get('query_results', {}).items():
            message += f"""
            <tr>
                <td><strong>{table_name}:</strong></td>
                <td>{result}</td>
            </tr>
            """

        message += "</table>"

        if backup_info.get('errors'):
            message += f"""
            <h3 style="color: red;">Error yang Ditemukan</h3>
            <ul>
            """
            for error in backup_info['errors']:
                message += f"<li>{error}</li>"
            message += "</ul>"

        subject = f"Backup Report - {backup_info.get('backup_date', datetime.now().strftime('%Y-%m-%d'))}"

        return self.send_notification(subject, message)

    def send_alert(self, alert_type, message):
        """
        Kirim alert untuk masalah tertentu
        """
        subject = f"ALERT - {alert_type}"
        alert_message = f"""
        <div style="background-color: #ffcccc; padding: 15px; border-radius: 5px;">
            <h3 style="color: red;">⚠️ {alert_type}</h3>
            <p>{message}</p>
            <p><strong>Waktu:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """

        return self.send_notification(subject, alert_message)