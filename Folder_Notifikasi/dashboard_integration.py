#!/usr/bin/env python3
"""
Dashboard Integration Script
- Integrasi dashboard monitoring dengan sync yang proper
- Memastikan semua komponen UI berjalan harmonis
- Auto-sync data antar tabs dan components
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import threading
import time
import logging

class DashboardIntegrator:
    """
    Integrator untuk dashboard monitoring yang sync proper
    antara semua komponen UI
    """

    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.logger = logging.getLogger('DashboardIntegrator')

        # Data synchronization
        self.summary_data = {}
        self.dashboard_cache = {}
        self.last_sync_time = None

        # Auto-refresh settings
        self.auto_refresh_enabled = True
        self.refresh_interval = 30  # seconds
        self.sync_thread = None
        self.sync_running = False

        # Event handlers
        self.event_handlers = {}

        # Initialize integration
        self.setup_integration()

    def setup_integration(self):
        """Setup dashboard integration"""
        self.logger.info("Setting up dashboard integration...")

        # Register event handlers
        self.register_event_handlers()

        # Start auto-sync
        self.start_auto_sync()

        # Load initial data
        self.load_initial_data()

        self.logger.info("Dashboard integration setup completed")

    def register_event_handlers(self):
        """Register event handlers for data synchronization"""
        self.event_handlers = {
            'data_loaded': self.on_data_loaded,
            'data_updated': self.on_data_updated,
            'monitoring_started': self.on_monitoring_started,
            'monitoring_stopped': self.on_monitoring_stopped,
            'scan_completed': self.on_scan_completed,
            'email_sent': self.on_email_sent
        }

    def start_auto_sync(self):
        """Start auto-synchronization thread"""
        if not self.sync_running:
            self.sync_running = True
            self.sync_thread = threading.Thread(target=self.sync_loop, daemon=True)
            self.sync_thread.start()
            self.logger.info("Auto-sync started")

    def stop_auto_sync(self):
        """Stop auto-synchronization"""
        self.sync_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        self.logger.info("Auto-sync stopped")

    def sync_loop(self):
        """Main synchronization loop"""
        while self.sync_running:
            try:
                if self.auto_refresh_enabled:
                    self.perform_sync()

                # Wait for next sync
                time.sleep(self.refresh_interval)

            except Exception as e:
                self.logger.error(f"Error in sync loop: {str(e)}")
                time.sleep(5)

    def perform_sync(self):
        """Perform data synchronization"""
        try:
            # Load latest data
            self.load_backup_data()

            # Update dashboard cache
            self.update_dashboard_cache()

            # Trigger UI updates
            self.trigger_ui_updates()

            # Update last sync time
            self.last_sync_time = datetime.now()

        except Exception as e:
            self.logger.error(f"Error performing sync: {str(e)}")

    def load_initial_data(self):
        """Load initial data"""
        try:
            self.load_backup_data()
            self.trigger_event('data_loaded', self.summary_data)
        except Exception as e:
            self.logger.error(f"Error loading initial data: {str(e)}")

    def load_backup_data(self):
        """Load backup data from JSON file"""
        try:
            json_file = "backup_summary_enhanced.json"

            if not os.path.exists(json_file):
                self.logger.warning(f"Backup data file not found: {json_file}")
                return

            with open(json_file, 'r', encoding='utf-8') as f:
                self.summary_data = json.load(f)

            self.logger.info(f"Loaded {len(self.summary_data)} backup records")

        except Exception as e:
            self.logger.error(f"Error loading backup data: {str(e)}")

    def update_dashboard_cache(self):
        """Update dashboard cache with latest data"""
        try:
            # Calculate metrics
            metrics = self.calculate_metrics()

            # Update cache
            self.dashboard_cache = {
                'metrics': metrics,
                'critical_alerts': self.calculate_critical_alerts(),
                'backup_status': self.calculate_backup_status(),
                'recent_activity': self.get_recent_activity(),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error updating dashboard cache: {str(e)}")

    def calculate_metrics(self):
        """Calculate dashboard metrics"""
        if not self.summary_data:
            return {}

        try:
            total_files = len(self.summary_data)
            valid_files = sum(1 for f in self.summary_data.values() if f.get('status') == 'Valid')
            invalid_files = total_files - valid_files

            # Calculate warnings
            warning_files = 0
            for file_info in self.summary_data.values():
                if file_info.get('is_outdated', False):
                    warning_files += 1

            # Get latest backup date
            dates = []
            for file_info in self.summary_data.values():
                modified = file_info.get('modified')
                if modified:
                    try:
                        dates.append(datetime.fromisoformat(modified.replace('Z', '+00:00')))
                    except:
                        pass

            latest_backup = max(dates) if dates else None
            oldest_backup = min(dates) if dates else None

            # Calculate system health
            system_health = self.calculate_system_health(valid_files, total_files, warning_files)

            return {
                'total_files': total_files,
                'valid_files': valid_files,
                'invalid_files': invalid_files,
                'warning_files': warning_files,
                'latest_backup': latest_backup.isoformat() if latest_backup else None,
                'oldest_backup': oldest_backup.isoformat() if oldest_backup else None,
                'system_health': system_health,
                'backup_types': self.get_backup_types_distribution(),
                'size_distribution': self.get_size_distribution()
            }

        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")
            return {}

    def calculate_system_health(self, valid_files, total_files, warning_files):
        """Calculate overall system health"""
        try:
            if total_files == 0:
                return 'unknown'

            success_rate = valid_files / total_files

            if success_rate >= 0.9 and warning_files == 0:
                return 'excellent'
            elif success_rate >= 0.7:
                return 'good'
            elif success_rate >= 0.5:
                return 'fair'
            else:
                return 'poor'

        except Exception as e:
            self.logger.error(f"Error calculating system health: {str(e)}")
            return 'unknown'

    def get_backup_types_distribution(self):
        """Get distribution of backup types"""
        try:
            types = {}
            for file_info in self.summary_data.values():
                backup_type = file_info.get('backup_type', 'Unknown')
                types[backup_type] = types.get(backup_type, 0) + 1

            return types

        except Exception as e:
            self.logger.error(f"Error getting backup types distribution: {str(e)}")
            return {}

    def get_size_distribution(self):
        """Get size distribution of backup files"""
        try:
            sizes = []
            for file_info in self.summary_data.values():
                size = file_info.get('size', 0)
                sizes.append(size)

            if not sizes:
                return {}

            total_size = sum(sizes)
            avg_size = total_size / len(sizes)

            return {
                'total_size': total_size,
                'average_size': avg_size,
                'min_size': min(sizes),
                'max_size': max(sizes),
                'file_count': len(sizes)
            }

        except Exception as e:
            self.logger.error(f"Error getting size distribution: {str(e)}")
            return {}

    def calculate_critical_alerts(self):
        """Calculate critical alerts"""
        try:
            alerts = []

            for file_path, file_info in self.summary_data.items():
                # Check for invalid files
                if file_info.get('status') != 'Valid':
                    alerts.append({
                        'type': 'invalid_file',
                        'file': os.path.basename(file_path),
                        'severity': 'high',
                        'message': f"Invalid backup file: {os.path.basename(file_path)}"
                    })

                # Check for outdated files
                if file_info.get('is_outdated', False):
                    alerts.append({
                        'type': 'outdated_file',
                        'file': os.path.basename(file_path),
                        'severity': 'medium',
                        'message': f"Outdated backup file: {os.path.basename(file_path)}"
                    })

                # Check for size warnings
                bak_files = file_info.get('bak_files', [])
                for bak in bak_files:
                    if bak.get('size_warning', False):
                        alerts.append({
                            'type': 'size_warning',
                            'file': bak.get('filename', 'Unknown'),
                            'severity': 'medium',
                            'message': f"Size warning for: {bak.get('filename', 'Unknown')}"
                        })

            return alerts

        except Exception as e:
            self.logger.error(f"Error calculating critical alerts: {str(e)}")
            return []

    def calculate_backup_status(self):
        """Calculate backup status overview"""
        try:
            status_overview = {}

            for file_path, file_info in self.summary_data.items():
                status = file_info.get('status', 'Unknown')
                filename = os.path.basename(file_path)

                status_overview[filename] = {
                    'status': status,
                    'size': file_info.get('size', 0),
                    'modified': file_info.get('modified'),
                    'backup_type': file_info.get('backup_type', 'Unknown'),
                    'path': file_path
                }

            return status_overview

        except Exception as e:
            self.logger.error(f"Error calculating backup status: {str(e)}")
            return {}

    def get_recent_activity(self):
        """Get recent activity log"""
        try:
            activities = []

            # Add data load activity
            if self.last_sync_time:
                activities.append({
                    'timestamp': self.last_sync_time,
                    'type': 'data_sync',
                    'message': f'Data synchronized - {len(self.summary_data)} files loaded'
                })

            # Add file scan activities
            for file_path, file_info in self.summary_data.items():
                modified = file_info.get('modified')
                if modified:
                    try:
                        mod_time = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                        activities.append({
                            'timestamp': mod_time.isoformat(),
                            'type': 'file_modified',
                            'message': f'File modified: {os.path.basename(file_path)}'
                        })
                    except:
                        pass

            # Sort by timestamp and return latest 10
            activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return activities[:10]

        except Exception as e:
            self.logger.error(f"Error getting recent activity: {str(e)}")
            return []

    def trigger_ui_updates(self):
        """Trigger UI updates across all components"""
        try:
            # Update dashboard metrics
            self.update_dashboard_metrics()

            # Update critical alerts
            self.update_critical_alerts_display()

            # Update backup status
            self.update_backup_status_display()

            # Update recent activity
            self.update_recent_activity_display()

            # Log sync activity
            self.logger.info("UI updates triggered")

        except Exception as e:
            self.logger.error(f"Error triggering UI updates: {str(e)}")

    def update_dashboard_metrics(self):
        """Update dashboard metrics display"""
        try:
            if hasattr(self.parent_app, 'update_dashboard_metrics'):
                self.parent_app.update_dashboard_metrics(self.dashboard_cache.get('metrics', {}))
        except Exception as e:
            self.logger.error(f"Error updating dashboard metrics: {str(e)}")

    def update_critical_alerts_display(self):
        """Update critical alerts display"""
        try:
            if hasattr(self.parent_app, 'update_critical_alerts'):
                alerts = self.dashboard_cache.get('critical_alerts', [])
                self.parent_app.update_critical_alerts(alerts)
        except Exception as e:
            self.logger.error(f"Error updating critical alerts display: {str(e)}")

    def update_backup_status_display(self):
        """Update backup status display"""
        try:
            if hasattr(self.parent_app, 'update_backup_status'):
                status = self.dashboard_cache.get('backup_status', {})
                self.parent_app.update_backup_status(status)
        except Exception as e:
            self.logger.error(f"Error updating backup status display: {str(e)}")

    def update_recent_activity_display(self):
        """Update recent activity display"""
        try:
            if hasattr(self.parent_app, 'update_recent_activity'):
                activity = self.dashboard_cache.get('recent_activity', [])
                self.parent_app.update_recent_activity(activity)
        except Exception as e:
            self.logger.error(f"Error updating recent activity display: {str(e)}")

    def trigger_event(self, event_type, data=None):
        """Trigger event to registered handlers"""
        try:
            if event_type in self.event_handlers:
                handler = self.event_handlers[event_type]
                if handler:
                    handler(data)

        except Exception as e:
            self.logger.error(f"Error triggering event {event_type}: {str(e)}")

    def on_data_loaded(self, data):
        """Handle data loaded event"""
        try:
            self.logger.info(f"Data loaded event triggered with {len(data) if data else 0} records")
            self.trigger_ui_updates()
        except Exception as e:
            self.logger.error(f"Error handling data loaded event: {str(e)}")

    def on_data_updated(self, data):
        """Handle data updated event"""
        try:
            self.logger.info("Data updated event triggered")
            self.update_dashboard_cache()
            self.trigger_ui_updates()
        except Exception as e:
            self.logger.error(f"Error handling data updated event: {str(e)}")

    def on_monitoring_started(self, data):
        """Handle monitoring started event"""
        try:
            self.logger.info("Monitoring started event triggered")
            self.auto_refresh_enabled = True
        except Exception as e:
            self.logger.error(f"Error handling monitoring started event: {str(e)}")

    def on_monitoring_stopped(self, data):
        """Handle monitoring stopped event"""
        try:
            self.logger.info("Monitoring stopped event triggered")
            # Keep auto-refresh enabled even when monitoring stops
        except Exception as e:
            self.logger.error(f"Error handling monitoring stopped event: {str(e)}")

    def on_scan_completed(self, data):
        """Handle scan completed event"""
        try:
            self.logger.info("Scan completed event triggered")
            self.load_backup_data()
            self.trigger_ui_updates()
        except Exception as e:
            self.logger.error(f"Error handling scan completed event: {str(e)}")

    def on_email_sent(self, data):
        """Handle email sent event"""
        try:
            self.logger.info("Email sent event triggered")
            # Add activity log
            activity = {
                'timestamp': datetime.now().isoformat(),
                'type': 'email_sent',
                'message': 'Email report sent successfully'
            }

            if 'recent_activity' in self.dashboard_cache:
                self.dashboard_cache['recent_activity'].insert(0, activity)
                self.dashboard_cache['recent_activity'] = self.dashboard_cache['recent_activity'][:10]

            self.update_recent_activity_display()

        except Exception as e:
            self.logger.error(f"Error handling email sent event: {str(e)}")

    def get_dashboard_data(self):
        """Get current dashboard data"""
        return self.dashboard_cache

    def get_backup_summary(self):
        """Get backup summary data"""
        return self.summary_data

    def force_refresh(self):
        """Force refresh of all data"""
        try:
            self.logger.info("Force refresh triggered")
            self.perform_sync()
            messagebox.showinfo("Refresh", "Dashboard data refreshed successfully")
        except Exception as e:
            self.logger.error(f"Error during force refresh: {str(e)}")
            messagebox.showerror("Refresh Error", f"Error during refresh: {str(e)}")

    def export_dashboard_state(self):
        """Export current dashboard state"""
        try:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'summary_data': self.summary_data,
                'dashboard_cache': self.dashboard_cache,
                'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None
            }

            filename = f"dashboard_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Dashboard state exported to {filename}")
            return filename

        except Exception as e:
            self.logger.error(f"Error exporting dashboard state: {str(e)}")
            return None

    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_auto_sync()
            self.logger.info("Dashboard integration cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


# ============= USAGE EXAMPLE =============

def example_usage():
    """Example of how to use the DashboardIntegrator"""

    class MockParentApp:
        def __init__(self):
            self.dashboard_metrics_updated = False
            self.critical_alerts_updated = False
            self.backup_status_updated = False
            self.recent_activity_updated = False

        def update_dashboard_metrics(self, metrics):
            """Mock method to update dashboard metrics"""
            print(f"Dashboard metrics updated: {metrics}")
            self.dashboard_metrics_updated = True

        def update_critical_alerts(self, alerts):
            """Mock method to update critical alerts"""
            print(f"Critical alerts updated: {len(alerts)} alerts")
            self.critical_alerts_updated = True

        def update_backup_status(self, status):
            """Mock method to update backup status"""
            print(f"Backup status updated: {len(status)} files")
            self.backup_status_updated = True

        def update_recent_activity(self, activity):
            """Mock method to update recent activity"""
            print(f"Recent activity updated: {len(activity)} activities")
            self.recent_activity_updated = True

    # Create mock parent app
    parent_app = MockParentApp()

    # Create integrator
    integrator = DashboardIntegrator(parent_app)

    # Let it run for a few seconds
    time.sleep(2)

    # Force refresh
    integrator.force_refresh()

    # Export state
    export_file = integrator.export_dashboard_state()
    if export_file:
        print(f"Dashboard state exported to: {export_file}")

    # Cleanup
    integrator.cleanup()

    print("Example usage completed!")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run example
    example_usage()