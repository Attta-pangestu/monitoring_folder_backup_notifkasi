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

        # Default values
        self.sender_email = ''
        self.sender_password = ''
        self.receiver_email = ''
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.default_subject = 'Laporan Monitoring Backup Database'

        # Load from config if exists
        try:
            self.config.read(self.config_path)
            if 'EMAIL' in self.config:
                self.sender_email = self.config['EMAIL'].get('sender_email', self.sender_email)
                self.sender_password = self.config['EMAIL'].get('sender_password', self.sender_password)
                self.receiver_email = self.config['EMAIL'].get('receiver_email', self.receiver_email)
                self.smtp_server = self.config['EMAIL'].get('smtp_server', self.smtp_server)
                self.smtp_port = int(self.config['EMAIL'].get('smtp_port', self.smtp_port))
            if 'NOTIFICATION' in self.config:
                self.default_subject = self.config['NOTIFICATION'].get('subject', self.default_subject)
        except Exception as e:
            print(f"Warning: Could not load email config: {e}")

    def send_notification(self, subject=None, message="", attachment_path=None):
        """
        Kirim email notifikasi
        """
        # Validate required fields
        if not self.sender_email or not self.sender_password or not self.receiver_email:
            return False, "Konfigurasi email tidak lengkap. Silakan periksa email pengirim, password, dan email penerima."

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

            # Login with error handling
            try:
                server.login(self.sender_email, self.sender_password)
            except smtplib.SMTPAuthenticationError as auth_error:
                server.quit()
                return False, f"Autentikasi gagal: {str(auth_error)}. Silakan periksa email dan app password Anda."

            text = msg.as_string()
            server.sendmail(self.sender_email, self.receiver_email, text)
            server.quit()

            return True, "Email berhasil dikirim"

        except smtplib.SMTPException as smtp_error:
            return False, f"Error SMTP: {str(smtp_error)}"
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

        <h3>Hasil Query</h3>
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

        subject = f"Laporan Backup - {backup_info.get('backup_date', datetime.now().strftime('%Y-%m-%d'))}"

        return self.send_notification(subject, message)

    def send_alert(self, alert_type, message):
        """
        Kirim alert untuk masalah tertentu
        """
        subject = f"PERINGATAN - {alert_type}"
        alert_message = f"""
        <div style="background-color: #ffcccc; padding: 15px; border-radius: 5px;">
            <h3 style="color: red;">⚠️ {alert_type}</h3>
            <p>{message}</p>
            <p><strong>Waktu:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        """

        return self.send_notification(subject, alert_message)

    def send_monitoring_report(self, monitoring_data):
        """
        Kirim monitoring report untuk multiple backup files
        monitoring_data: dict containing monitoring information for multiple files
        """
        monitoring_date = monitoring_data.get('monitoring_date', 'Unknown')
        analysis_time = monitoring_data.get('analysis_time', '')
        total_files = monitoring_data.get('total_files', 0)
        summary = monitoring_data.get('summary', {})
        files = monitoring_data.get('files', {})

        message = f"""
        <h3>Laporan Monitoring Backup Database</h3>
        <p><strong>Tanggal Monitoring:</strong> {monitoring_date}</p>
        <p><strong>Waktu Analisis:</strong> {analysis_time}</p>
        <p><strong>Total Files:</strong> {total_files}</p>

        <h4>Ringkasan</h4>
        <table border="1" style="border-collapse: collapse;">
            <tr>
                <td><strong>File Sehat:</strong></td>
                <td style="color: green;">{summary.get('healthy_files', 0)}</td>
            </tr>
            <tr>
                <td><strong>File Bermasalah:</strong></td>
                <td style="color: red;">{summary.get('files_with_issues', 0)}</td>
            </tr>
            <tr>
                <td><strong>Overall Assessment:</strong></td>
                <td>{summary.get('overall_assessment', 'Unknown')}</td>
            </tr>
        </table>

        <h4>Detail File</h4>
        <table border="1" style="border-collapse: collapse;">
            <tr>
                <th><strong>Nama File</strong></th>
                <th><strong>Ukuran (MB)</strong></th>
                <th><strong>Modified</strong></th>
                <th><strong>ZIP Valid</strong></th>
                <th><strong>Extracted</strong></th>
                <th><strong>BAK Files</strong></th>
                <th><strong>Status</strong></th>
            </tr>
        """

        for file_name, file_info in files.items():
            status_color = "green" if file_info.get('overall_status') == 'healthy' else "red"
            extractable_status = "Ya" if file_info.get('extractable', False) else "Tidak"

            # Get additional info from monitoring results
            monitoring_result = monitoring_data.get('files', {}).get(file_name, {})
            extracted_files_count = monitoring_result.get('extracted_files_count', 0)
            zip_valid = monitoring_result.get('zip_valid', False)

            message += f"""
            <tr>
                <td>{file_name}</td>
                <td>{file_info.get('size_mb', 0):.2f}</td>
                <td>{file_info.get('modified_time', '')}</td>
                <td style="color: {'green' if zip_valid else 'red'};">{'Ya' if zip_valid else 'Tidak'}</td>
                <td>{extracted_files_count}</td>
                <td>{file_info.get('bak_files_count', 0)}</td>
                <td style="color: {status_color};">{file_info.get('overall_status', 'unknown')}</td>
            </tr>
            """

        message += "</table>"

        # Add recommendations
        if summary.get('files_with_issues', 0) > 0:
            message += """
            <h4 style="color: red;">Rekomendasi</h4>
            <ul>
                <li>Periksa file yang bermasalah untuk corruption detection</li>
                <li>Verifikasi backup integrity dan restore capability</li>
                <li>Pertimbangkan untuk membuat backup baru jika issues persist</li>
            </ul>
            """
        else:
            message += """
            <h4 style="color: green;">Status Sistem</h4>
            <p>Semua file backup dalam kondisi sehat dan terkonfigurasi dengan benar.</p>
            """

        subject = f"Laporan Monitoring Backup - {monitoring_date}"
        return self.send_notification(subject, message)