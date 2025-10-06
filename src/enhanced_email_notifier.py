#!/usr/bin/env python3
"""
Enhanced Email Notifier for Backup Analysis
Pengirim email notifikasi dengan laporan komprehensif backup analysis
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import configparser
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

class EnhancedEmailNotifier:
    def __init__(self, config_file='config/config.ini'):
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)

        # Default values
        self.sender_email = ''
        self.sender_password = ''
        self.receiver_email = ''
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.default_subject = 'Backup Database Analysis Report'

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

    def send_comprehensive_backup_report(self, analysis_data: Dict[str, Any], pdf_path: Optional[str] = None) -> tuple:
        """
        Kirim laporan komprehensif backup analysis

        Args:
            analysis_data: Data hasil analisis backup
            pdf_path: Path ke file PDF report (optional)

        Returns:
            tuple (success: bool, message: str)
        """
        try:
            # Validate required fields
            if not self.sender_email or not self.sender_password or not self.receiver_email:
                return False, "Konfigurasi email tidak lengkap. Silakan periksa email pengirim, password, dan email penerima."

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email

            # Generate subject
            report_time = analysis_data.get('analysis_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            subject = f"{self.default_subject} - {report_time}"
            msg['Subject'] = subject

            # Generate HTML body
            html_body = self._generate_comprehensive_html_report(analysis_data)
            msg.attach(MIMEText(html_body, 'html'))

            # Attach PDF if provided
            if pdf_path and os.path.exists(pdf_path):
                self._attach_pdf(msg, pdf_path)

            # Connect to SMTP server and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.ehlo()

            # Login with error handling
            try:
                server.login(self.sender_email, self.sender_password)
            except smtplib.SMTPAuthenticationError as auth_error:
                server.quit()
                return False, f"Autentikasi gagal: {str(auth_error)}. Silakan periksa email dan app password Anda."

            text = msg.as_string()
            server.sendmail(self.sender_email, self.receiver_email, text)
            server.quit()

            return True, "Email laporan komprehensif berhasil dikirim"

        except smtplib.SMTPException as smtp_error:
            return False, f"Error SMTP: {str(smtp_error)}"
        except Exception as e:
            return False, f"Gagal mengirim email: {str(e)}"

    def _generate_comprehensive_html_report(self, analysis_data: Dict[str, Any]) -> str:
        """Generate HTML report from analysis data"""

        # Extract summary information
        zip_info = analysis_data.get('zip_info', {})
        validation = analysis_data.get('validation', {})
        bak_analysis = analysis_data.get('bak_analysis', {})
        file_analysis = analysis_data.get('file_analysis', {})

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .section {{ margin-bottom: 25px; border-left: 4px solid #007bff; padding-left: 15px; }}
                .success {{ border-left-color: #28a745; }}
                .warning {{ border-left-color: #ffc107; }}
                .danger {{ border-left-color: #dc3545; }}
                .info {{ border-left-color: #17a2b8; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .status-good {{ color: #28a745; font-weight: bold; }}
                .status-warning {{ color: #ffc107; font-weight: bold; }}
                .status-danger {{ color: #dc3545; font-weight: bold; }}
                .recommendation {{ background-color: #e7f3ff; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Komprehensif Backup Database Analysis Report</h2>
                <p><strong>Report Time:</strong> {analysis_data.get('analysis_time', 'Unknown')}</p>
                <p><strong>Generated by:</strong> Backup Monitor System</p>
            </div>
        """

        # 1. ZIP File Summary
        html += f"""
        <div class="section info">
            <h3>📦 ZIP File Summary</h3>
            <table>
                <tr><td><strong>Filename:</strong></td><td>{zip_info.get('filename', 'Unknown')}</td></tr>
                <tr><td><strong>File Size:</strong></td><td>{zip_info.get('file_size_mb', 0):.2f} MB</td></tr>
                <tr><td><strong>Created:</strong></td><td>{zip_info.get('created_time', 'Unknown')}</td></tr>
                <tr><td><strong>Modified:</strong></td><td>{zip_info.get('modified_time', 'Unknown')}</td></tr>
                <tr><td><strong>Backup Date (from filename):</strong></td><td>{zip_info.get('backup_date_from_filename', 'Unknown')}</td></tr>
                <tr><td><strong>Database Type:</strong></td><td>{zip_info.get('database_type_from_filename', 'Unknown')}</td></tr>
                <tr><td><strong>Total Files in ZIP:</strong></td><td>{zip_info.get('total_files', 0)}</td></tr>
                <tr><td><strong>Compression Ratio:</strong></td><td>{zip_info.get('compression_ratio', 0):.1f}%</td></tr>
            </table>
        </div>
        """

        # 2. ZIP Validation Status
        validation_status = validation.get('file_integrity', 'Unknown')
        status_class = {
            'Good': 'status-good',
            'Warnings': 'status-warning',
            'Corrupted': 'status-danger',
            'Invalid': 'status-danger',
            'Error': 'status-danger'
        }.get(validation_status, 'status-warning')

        html += f"""
        <div class="section {validation.get('file_integrity', 'Unknown').lower()}">
            <h3>✅ ZIP Validation Status</h3>
            <table>
                <tr><td><strong>ZIP Valid:</strong></td><td class="{status_class}">{validation.get('is_valid_zip', False)}</td></tr>
                <tr><td><strong>Can Be Extracted:</strong></td><td class="{status_class}">{validation.get('can_be_extracted', False)}</td></tr>
                <tr><td><strong>File Integrity:</strong></td><td class="{status_class}">{validation_status}</td></tr>
                <tr><td><strong>Corruption Detected:</strong></td><td class="{status_class}">{validation.get('corruption_detected', False)}</td></tr>
            </table>
        """

        if validation.get('warnings'):
            html += "<h4>Warnings:</h4><ul>"
            for warning in validation['warnings']:
                html += f"<li>{warning}</li>"
            html += "</ul>"

        html += "</div>"

        # 3. BAK Files Analysis
        if bak_analysis.get('total_bak_files', 0) > 0:
            html += f"""
            <div class="section info">
                <h3>💾 BAK Files Analysis</h3>
                <table>
                    <tr><td><strong>Total BAK Files:</strong></td><td>{bak_analysis.get('total_bak_files', 0)}</td></tr>
                    <tr><td><strong>Total BAK Size:</strong></td><td>{bak_analysis.get('summary', {}).get('total_size_mb', 0):.2f} MB</td></tr>
                    <tr><td><strong>Valid BAK Files:</strong></td><td class="status-good">{bak_analysis.get('summary', {}).get('valid_bak_files', 0)}</td></tr>
                    <tr><td><strong>Corrupted BAK Files:</strong></td><td class="status-danger">{bak_analysis.get('summary', {}).get('corrupted_bak_files', 0)}</td></tr>
                </table>
            """

            # Detailed BAK analysis
            html += "<h4>Detailed BAK File Analysis:</h4>"
            for bak_result in bak_analysis.get('bak_analyses', []):
                bak_filename = bak_result.get('original_filename', bak_result.get('filename', 'Unknown'))
                db_info = bak_result.get('database_info', {})
                validation = bak_result.get('validation', {})

                html += f"""
                <table style="margin-left: 20px; margin-bottom: 15px;">
                    <tr><th colspan="2" style="background-color: #f8f9fa;">{bak_filename}</th></tr>
                    <tr><td><strong>Database Name:</strong></td><td>{db_info.get('database_name', 'Unknown')}</td></tr>
                    <tr><td><strong>File Size:</strong></td><td>{bak_result.get('file_size_mb', 0):.2f} MB</td></tr>
                    <tr><td><strong>Backup Type:</strong></td><td>{db_info.get('backup_type', 'Unknown')}</td></tr>
                    <tr><td><strong>Backup Date:</strong></td><td>{db_info.get('backup_date', 'Unknown')}</td></tr>
                    <tr><td><strong>SQL Version:</strong></td><td>{db_info.get('sql_version', 'Unknown')}</td></tr>
                    <tr><td><strong>Estimated Tables:</strong></td><td>{db_info.get('estimated_tables', 0)}</td></tr>
                    <tr><td><strong>Estimated Records:</strong></td><td>{bak_result.get('table_info', {}).get('total_records', db_info.get('estimated_records', 0)):,}</td></tr>
                    <tr><td><strong>BAK Valid:</strong></td><td class="{'status-good' if validation.get('is_valid_bak') else 'status-danger'}">{validation.get('is_valid_bak', False)}</td></tr>
                    <tr><td><strong>Can Be Restored:</strong></td><td class="{'status-good' if validation.get('can_be_restored') else 'status-danger'}">{validation.get('can_be_restored', False)}</td></tr>
                </table>
                """

            html += "</div>"

        # 4. File Content Analysis
        if file_analysis:
            html += f"""
            <div class="section info">
                <h3>📋 File Content Analysis</h3>
                <table>
                    <tr><td><strong>Total Files:</strong></td><td>{file_analysis.get('total_files', 0)}</td></tr>
                    <tr><td><strong>BAK Files:</strong></td><td>{len(file_analysis.get('bak_files', []))}</td></tr>
                    <tr><td><strong>Database Files:</strong></td><td>{len(file_analysis.get('database_files', []))}</td></tr>
                    <tr><td><strong>Log Files:</strong></td><td>{len(file_analysis.get('log_files', []))}</td></tr>
                </table>
            """

            # Show largest files
            largest_files = file_analysis.get('largest_files', [])[:5]
            if largest_files:
                html += "<h4>Largest Files:</h4><table>"
                for file_info in largest_files:
                    html += f"""
                    <tr>
                        <td>{file_info.get('filename', 'Unknown')}</td>
                        <td>{file_info.get('size_mb', 0):.2f} MB</td>
                        <td>{file_info.get('file_type', 'Unknown')}</td>
                    </tr>
                    """
                html += "</table>"

            html += "</div>"

        # 5. Recommendations
        recommendations = analysis_data.get('recommendations', [])
        if recommendations:
            html += """
            <div class="section warning">
                <h3>💡 Recommendations</h3>
            """
            for rec in recommendations:
                html += f'<div class="recommendation">{rec}</div>'
            html += "</div>"

        # 6. Footer
        html += f"""
            <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; text-align: center;">
                <p><em>This report was automatically generated by the Backup Database Monitor System</em></p>
                <p><strong>Report Time:</strong> {analysis_data.get('analysis_time', 'Unknown')}</p>
                <p><small>For questions or issues, please contact the system administrator</small></p>
            </div>
        </body>
        </html>
        """

        return html

    def _attach_pdf(self, msg: MIMEMultipart, pdf_path: str):
        """Attach PDF file to email"""
        try:
            with open(pdf_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(pdf_path)}'
            )
            msg.attach(part)
        except Exception as e:
            print(f"Warning: Could not attach PDF: {e}")

    def send_auto_analysis_report(self, analysis_results: List[Dict[str, Any]], pdf_path: Optional[str] = None) -> tuple:
        """
        Kirim laporan auto analysis untuk multiple ZIP files

        Args:
            analysis_results: List hasil analisis multiple ZIP files
            pdf_path: Path ke file PDF report (optional)
        """
        try:
            # Validate required fields
            if not self.sender_email or not self.sender_password or not self.receiver_email:
                return False, "Konfigurasi email tidak lengkap"

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email

            report_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            subject = f"Auto Backup Analysis Report - {len(analysis_results)} Files"
            msg['Subject'] = subject

            # Generate HTML body for multiple files
            html_body = self._generate_multi_file_html_report(analysis_results)
            msg.attach(MIMEText(html_body, 'html'))

            # Attach PDF if provided
            if pdf_path and os.path.exists(pdf_path):
                self._attach_pdf(msg, pdf_path)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.ehlo()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, self.receiver_email, msg.as_string())
            server.quit()

            return True, "Auto analysis report berhasil dikirim"

        except Exception as e:
            return False, f"Gagal mengirim auto analysis report: {str(e)}"

    def _generate_multi_file_html_report(self, analysis_results: List[Dict[str, Any]]) -> str:
        """Generate HTML report for multiple files analysis"""

        # Calculate summary statistics
        total_files = len(analysis_results)
        successful_analyses = len([r for r in analysis_results if r.get('analysis_status', '').lower() != 'failed'])
        total_size_mb = sum(r.get('zip_info', {}).get('file_size_mb', 0) for r in analysis_results)
        valid_zips = len([r for r in analysis_results if r.get('validation', {}).get('is_valid_zip', False)])
        corrupted_files = len([r for r in analysis_results if r.get('validation', {}).get('corruption_detected', False)])

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .summary {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .file-section {{ margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .status-good {{ color: #28a745; font-weight: bold; }}
                .status-warning {{ color: #ffc107; font-weight: bold; }}
                .status-danger {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Auto Backup Analysis Report</h2>
                <p><strong>Report Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Analyzed Files:</strong> {total_files}</p>
            </div>

            <div class="summary">
                <h3>📈 Summary Statistics</h3>
                <table>
                    <tr><td><strong>Total Files Analyzed:</strong></td><td>{total_files}</td></tr>
                    <tr><td><strong>Successful Analyses:</strong></td><td class="status-good">{successful_analyses}</td></tr>
                    <tr><td><strong>Failed Analyses:</strong></td><td class="status-danger">{total_files - successful_analyses}</td></tr>
                    <tr><td><strong>Total Size:</strong></td><td>{total_size_mb:.2f} MB</td></tr>
                    <tr><td><strong>Valid ZIP Files:</strong></td><td class="status-good">{valid_zips}</td></tr>
                    <tr><td><strong>Corrupted Files:</strong></td><td class="status-danger">{corrupted_files}</td></tr>
                </table>
            </div>
        """

        # Individual file results
        for i, result in enumerate(analysis_results, 1):
            zip_info = result.get('zip_info', {})
            validation = result.get('validation', {})
            bak_analysis = result.get('bak_analysis', {})

            status_class = 'file-section'
            if validation.get('corruption_detected'):
                status_class += ' status-danger'
            elif validation.get('warnings'):
                status_class += ' status-warning'

            html += f"""
            <div class="{status_class}">
                <h3>{i}. {zip_info.get('filename', 'Unknown')}</h3>
                <table>
                    <tr><td><strong>File Size:</strong></td><td>{zip_info.get('file_size_mb', 0):.2f} MB</td></tr>
                    <tr><td><strong>ZIP Status:</strong></td><td>{validation.get('file_integrity', 'Unknown')}</td></tr>
                    <tr><td><strong>BAK Files:</strong></td><td>{bak_analysis.get('total_bak_files', 0)}</td></tr>
                    <tr><td><strong>Backup Date:</strong></td><td>{zip_info.get('backup_date_from_filename', 'Unknown')}</td></tr>
                    <tr><td><strong>Databases Found:</strong></td><td>{', '.join(bak_analysis.get('summary', {}).get('databases_found', []))}</td></tr>
                </table>
            """

            # Show key recommendations for this file
            recommendations = result.get('recommendations', [])[:3]  # Show top 3
            if recommendations:
                html += "<h4>Key Recommendations:</h4><ul>"
                for rec in recommendations:
                    html += f"<li>{rec}</li>"
                html += "</ul>"

            html += "</div>"

        html += """
            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; text-align: center;">
                <p><em>Auto-generated backup analysis report</em></p>
                <p><small>Contact system administrator for questions</small></p>
            </div>
        </body>
        </html>
        """

        return html