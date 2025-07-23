"""
Preferences Dialog - Settings configuration for the torrent client
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QWidget, QLabel, QLineEdit, QPushButton, QSpinBox,
                             QCheckBox, QFormLayout, QGroupBox, QFileDialog,
                             QDialogButtonBox, QSlider, QComboBox)
from PyQt5.QtCore import Qt, QSettings

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("PyTorrent", "PyTorrent")
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # General tab
        self.create_general_tab(tab_widget)
        
        # Downloads tab
        self.create_downloads_tab(tab_widget)
        
        # Connection tab
        self.create_connection_tab(tab_widget)
        
        # Bandwidth tab
        self.create_bandwidth_tab(tab_widget)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        layout.addWidget(button_box)
        
    def create_general_tab(self, tab_widget):
        """Create general settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Startup group
        startup_group = QGroupBox("Startup")
        startup_layout = QFormLayout(startup_group)
        
        self.start_minimized_cb = QCheckBox("Start minimized")
        self.autostart_cb = QCheckBox("Start with system")
        
        startup_layout.addRow(self.start_minimized_cb)
        startup_layout.addRow(self.autostart_cb)
        
        layout.addWidget(startup_group)
        
        # Interface group
        interface_group = QGroupBox("Interface")
        interface_layout = QFormLayout(interface_group)
        
        self.confirm_exit_cb = QCheckBox("Confirm when exiting")
        self.confirm_delete_cb = QCheckBox("Confirm when deleting torrents")
        
        interface_layout.addRow(self.confirm_exit_cb)
        interface_layout.addRow(self.confirm_delete_cb)
        
        layout.addWidget(interface_group)
        
        layout.addStretch()
        tab_widget.addTab(widget, "General")
        
    def create_downloads_tab(self, tab_widget):
        """Create downloads settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Download directory group
        directory_group = QGroupBox("Download Directory")
        directory_layout = QFormLayout(directory_group)
        
        # Default download path
        path_layout = QHBoxLayout()
        self.download_path_edit = QLineEdit()
        path_browse_btn = QPushButton("Browse...")
        path_browse_btn.clicked.connect(self.browse_download_path)
        
        path_layout.addWidget(self.download_path_edit)
        path_layout.addWidget(path_browse_btn)
        
        directory_layout.addRow("Default location:", path_layout)
        
        # Auto-management
        self.auto_manage_cb = QCheckBox("Automatically manage torrents")
        directory_layout.addRow(self.auto_manage_cb)
        
        layout.addWidget(directory_group)
        
        # Completion group
        completion_group = QGroupBox("When Download Completes")
        completion_layout = QFormLayout(completion_group)
        
        self.seed_when_complete_cb = QCheckBox("Continue seeding")
        self.move_completed_cb = QCheckBox("Move completed downloads to:")
        
        # Completed downloads path
        completed_path_layout = QHBoxLayout()
        self.completed_path_edit = QLineEdit()
        completed_browse_btn = QPushButton("Browse...")
        completed_browse_btn.clicked.connect(self.browse_completed_path)
        
        completed_path_layout.addWidget(self.completed_path_edit)
        completed_path_layout.addWidget(completed_browse_btn)
        
        completion_layout.addRow(self.seed_when_complete_cb)
        completion_layout.addRow(self.move_completed_cb)
        completion_layout.addRow("", completed_path_layout)
        
        layout.addWidget(completion_group)
        
        layout.addStretch()
        tab_widget.addTab(widget, "Downloads")
        
    def create_connection_tab(self, tab_widget):
        """Create connection settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Port group
        port_group = QGroupBox("Listening Port")
        port_layout = QFormLayout(port_group)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(6881)
        
        self.random_port_cb = QCheckBox("Use random port on startup")
        self.upnp_cb = QCheckBox("Enable UPnP port mapping")
        
        port_layout.addRow("Port:", self.port_spin)
        port_layout.addRow(self.random_port_cb)
        port_layout.addRow(self.upnp_cb)
        
        layout.addWidget(port_group)
        
        # DHT group
        dht_group = QGroupBox("Distributed Hash Table (DHT)")
        dht_layout = QFormLayout(dht_group)
        
        self.enable_dht_cb = QCheckBox("Enable DHT")
        self.enable_lsd_cb = QCheckBox("Enable Local Service Discovery")
        
        dht_layout.addRow(self.enable_dht_cb)
        dht_layout.addRow(self.enable_lsd_cb)
        
        layout.addWidget(dht_group)
        
        # Connections group
        connections_group = QGroupBox("Connection Limits")
        connections_layout = QFormLayout(connections_group)
        
        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 1000)
        self.max_connections_spin.setValue(200)
        
        self.max_uploads_spin = QSpinBox()
        self.max_uploads_spin.setRange(1, 100)
        self.max_uploads_spin.setValue(4)
        
        connections_layout.addRow("Maximum connections:", self.max_connections_spin)
        connections_layout.addRow("Maximum uploads:", self.max_uploads_spin)
        
        layout.addWidget(connections_group)
        
        layout.addStretch()
        tab_widget.addTab(widget, "Connection")
        
    def create_bandwidth_tab(self, tab_widget):
        """Create bandwidth settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Global rate limits group
        global_group = QGroupBox("Global Rate Limits")
        global_layout = QFormLayout(global_group)
        
        # Download rate limit
        self.download_limit_cb = QCheckBox("Limit download rate to:")
        download_layout = QHBoxLayout()
        self.download_limit_spin = QSpinBox()
        self.download_limit_spin.setRange(1, 100000)
        self.download_limit_spin.setValue(1000)
        self.download_limit_spin.setSuffix(" KB/s")
        download_layout.addWidget(self.download_limit_spin)
        download_layout.addStretch()
        
        # Upload rate limit
        self.upload_limit_cb = QCheckBox("Limit upload rate to:")
        upload_layout = QHBoxLayout()
        self.upload_limit_spin = QSpinBox()
        self.upload_limit_spin.setRange(1, 100000)
        self.upload_limit_spin.setValue(100)
        self.upload_limit_spin.setSuffix(" KB/s")
        upload_layout.addWidget(self.upload_limit_spin)
        upload_layout.addStretch()
        
        global_layout.addRow(self.download_limit_cb)
        global_layout.addRow("", download_layout)
        global_layout.addRow(self.upload_limit_cb)
        global_layout.addRow("", upload_layout)
        
        layout.addWidget(global_group)
        
        # Alternative rate limits group
        alt_group = QGroupBox("Alternative Rate Limits")
        alt_layout = QFormLayout(alt_group)
        
        self.alt_limits_cb = QCheckBox("Enable alternative rate limits")
        
        # Alternative download rate
        alt_download_layout = QHBoxLayout()
        self.alt_download_spin = QSpinBox()
        self.alt_download_spin.setRange(1, 100000)
        self.alt_download_spin.setValue(500)
        self.alt_download_spin.setSuffix(" KB/s")
        alt_download_layout.addWidget(QLabel("Download:"))
        alt_download_layout.addWidget(self.alt_download_spin)
        alt_download_layout.addStretch()
        
        # Alternative upload rate
        alt_upload_layout = QHBoxLayout()
        self.alt_upload_spin = QSpinBox()
        self.alt_upload_spin.setRange(1, 100000)
        self.alt_upload_spin.setValue(50)
        self.alt_upload_spin.setSuffix(" KB/s")
        alt_upload_layout.addWidget(QLabel("Upload:"))
        alt_upload_layout.addWidget(self.alt_upload_spin)
        alt_upload_layout.addStretch()
        
        alt_layout.addRow(self.alt_limits_cb)
        alt_layout.addRow("", alt_download_layout)
        alt_layout.addRow("", alt_upload_layout)
        
        layout.addWidget(alt_group)
        
        layout.addStretch()
        tab_widget.addTab(widget, "Bandwidth")
        
    def browse_download_path(self):
        """Browse for default download directory"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", self.download_path_edit.text()
        )
        if path:
            self.download_path_edit.setText(path)
            
    def browse_completed_path(self):
        """Browse for completed downloads directory"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Completed Downloads Directory", self.completed_path_edit.text()
        )
        if path:
            self.completed_path_edit.setText(path)
            
    def load_settings(self):
        """Load settings from QSettings"""
        # General settings
        self.start_minimized_cb.setChecked(
            self.settings.value("general/start_minimized", False, type=bool)
        )
        self.autostart_cb.setChecked(
            self.settings.value("general/autostart", False, type=bool)
        )
        self.confirm_exit_cb.setChecked(
            self.settings.value("general/confirm_exit", True, type=bool)
        )
        self.confirm_delete_cb.setChecked(
            self.settings.value("general/confirm_delete", True, type=bool)
        )
        
        # Download settings
        default_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'PyTorrent')
        self.download_path_edit.setText(
            self.settings.value("downloads/default_path", default_path)
        )
        self.auto_manage_cb.setChecked(
            self.settings.value("downloads/auto_manage", True, type=bool)
        )
        self.seed_when_complete_cb.setChecked(
            self.settings.value("downloads/seed_when_complete", True, type=bool)
        )
        self.move_completed_cb.setChecked(
            self.settings.value("downloads/move_completed", False, type=bool)
        )
        self.completed_path_edit.setText(
            self.settings.value("downloads/completed_path", default_path)
        )
        
        # Connection settings
        self.port_spin.setValue(
            self.settings.value("connection/port", 6881, type=int)
        )
        self.random_port_cb.setChecked(
            self.settings.value("connection/random_port", False, type=bool)
        )
        self.upnp_cb.setChecked(
            self.settings.value("connection/upnp", True, type=bool)
        )
        self.enable_dht_cb.setChecked(
            self.settings.value("connection/enable_dht", True, type=bool)
        )
        self.enable_lsd_cb.setChecked(
            self.settings.value("connection/enable_lsd", True, type=bool)
        )
        self.max_connections_spin.setValue(
            self.settings.value("connection/max_connections", 200, type=int)
        )
        self.max_uploads_spin.setValue(
            self.settings.value("connection/max_uploads", 4, type=int)
        )
        
        # Bandwidth settings
        self.download_limit_cb.setChecked(
            self.settings.value("bandwidth/limit_download", False, type=bool)
        )
        self.download_limit_spin.setValue(
            self.settings.value("bandwidth/download_limit", 1000, type=int)
        )
        self.upload_limit_cb.setChecked(
            self.settings.value("bandwidth/limit_upload", False, type=bool)
        )
        self.upload_limit_spin.setValue(
            self.settings.value("bandwidth/upload_limit", 100, type=int)
        )
        self.alt_limits_cb.setChecked(
            self.settings.value("bandwidth/alt_limits", False, type=bool)
        )
        self.alt_download_spin.setValue(
            self.settings.value("bandwidth/alt_download", 500, type=int)
        )
        self.alt_upload_spin.setValue(
            self.settings.value("bandwidth/alt_upload", 50, type=int)
        )
        
    def save_settings(self):
        """Save settings to QSettings"""
        # General settings
        self.settings.setValue("general/start_minimized", self.start_minimized_cb.isChecked())
        self.settings.setValue("general/autostart", self.autostart_cb.isChecked())
        self.settings.setValue("general/confirm_exit", self.confirm_exit_cb.isChecked())
        self.settings.setValue("general/confirm_delete", self.confirm_delete_cb.isChecked())
        
        # Download settings
        self.settings.setValue("downloads/default_path", self.download_path_edit.text())
        self.settings.setValue("downloads/auto_manage", self.auto_manage_cb.isChecked())
        self.settings.setValue("downloads/seed_when_complete", self.seed_when_complete_cb.isChecked())
        self.settings.setValue("downloads/move_completed", self.move_completed_cb.isChecked())
        self.settings.setValue("downloads/completed_path", self.completed_path_edit.text())
        
        # Connection settings
        self.settings.setValue("connection/port", self.port_spin.value())
        self.settings.setValue("connection/random_port", self.random_port_cb.isChecked())
        self.settings.setValue("connection/upnp", self.upnp_cb.isChecked())
        self.settings.setValue("connection/enable_dht", self.enable_dht_cb.isChecked())
        self.settings.setValue("connection/enable_lsd", self.enable_lsd_cb.isChecked())
        self.settings.setValue("connection/max_connections", self.max_connections_spin.value())
        self.settings.setValue("connection/max_uploads", self.max_uploads_spin.value())
        
        # Bandwidth settings
        self.settings.setValue("bandwidth/limit_download", self.download_limit_cb.isChecked())
        self.settings.setValue("bandwidth/download_limit", self.download_limit_spin.value())
        self.settings.setValue("bandwidth/limit_upload", self.upload_limit_cb.isChecked())
        self.settings.setValue("bandwidth/upload_limit", self.upload_limit_spin.value())
        self.settings.setValue("bandwidth/alt_limits", self.alt_limits_cb.isChecked())
        self.settings.setValue("bandwidth/alt_download", self.alt_download_spin.value())
        self.settings.setValue("bandwidth/alt_upload", self.alt_upload_spin.value())
        
    def apply_settings(self):
        """Apply settings without closing dialog"""
        self.save_settings()
        
    def accept(self):
        """Accept dialog and save settings"""
        self.save_settings()
        super().accept() 