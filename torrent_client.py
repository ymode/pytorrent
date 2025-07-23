"""
Main Torrent Client Window
"""

import os
import sys
import time
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTreeWidget, QTreeWidgetItem, QMenuBar, QMenu, 
                             QAction, QToolBar, QStatusBar, QFileDialog, 
                             QInputDialog, QMessageBox, QProgressBar, QLabel,
                             QSplitter, QTextEdit, QPushButton, QFrame, QStyledItemDelegate,
                             QSystemTrayIcon, QApplication)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QThread, QRect, QUrl
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QPen, QDragEnterEvent, QDropEvent

from torrent_manager import TorrentManager
from add_torrent_dialog import AddTorrentDialog
from preferences_dialog import PreferencesDialog
from PyQt5.QtCore import QSettings

class ProgressBarDelegate(QStyledItemDelegate):
    """Custom delegate to draw progress bars in the tree widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter, option, index):
        # Only draw progress bars for the progress column (column 2)
        if index.column() == 2:
            # Get progress value and state
            progress_text = index.data(Qt.DisplayRole)
            torrent_state = index.data(Qt.UserRole) or 'Unknown'
            
            try:
                # Extract percentage from text like "45.2%"
                progress = float(progress_text.replace('%', '')) if progress_text and '%' in progress_text else 0
            except (ValueError, AttributeError):
                progress = 0
            
            # Set colors based on state
            if torrent_state.lower() in ['downloading', 'checking']:
                fill_color = QColor(52, 152, 219)  # Blue
            elif torrent_state.lower() in ['seeding', 'finished']:
                fill_color = QColor(46, 204, 113)  # Green
            elif torrent_state.lower() in ['paused']:
                fill_color = QColor(149, 165, 166)  # Gray
            elif torrent_state.lower() in ['error']:
                fill_color = QColor(231, 76, 60)  # Red
            else:
                fill_color = QColor(149, 165, 166)  # Default gray
            
            # Draw progress bar
            rect = option.rect.adjusted(4, 4, -4, -4)  # Add padding
            
            painter.save()
            
            # Draw background
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.fillRect(rect, QColor(240, 240, 240))
            painter.drawRect(rect)
            
            # Draw progress fill
            if progress > 0:
                fill_rect = QRect(rect.x(), rect.y(), 
                                int(rect.width() * progress / 100), rect.height())
                painter.fillRect(fill_rect, fill_color)
            
            # Draw progress text
            painter.setPen(QPen(QColor(0, 0, 0)))
            painter.drawText(rect, Qt.AlignCenter, f"{progress:.1f}%")
            
            painter.restore()
        else:
            # Use default painting for other columns
            super().paint(painter, option, index)

class TorrentClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.torrent_manager = TorrentManager()
        self.torrent_manager.torrent_added.connect(self.on_torrent_added)
        self.torrent_manager.torrent_updated.connect(self.on_torrent_updated)
        self.torrent_manager.torrent_removed.connect(self.on_torrent_removed)
        self.torrent_manager.error_occurred.connect(self.on_error_occurred)
        self.torrent_manager.torrent_completed.connect(self.on_torrent_completed)
        
        self.init_ui()
        self.setup_timer()
        self.setup_system_tray()
        
        # Apply saved settings on startup
        self.apply_preferences_to_manager()
        
    def show_context_menu(self, position):
        """Show context menu for torrent list"""
        item = self.torrent_list.itemAt(position)
        if not item:
            return
            
        # Create context menu
        context_menu = QMenu(self)
        
        # Get torrent info
        torrent_hash = item.data(0, Qt.UserRole)
        torrent_info = self.torrent_manager.get_torrent_info(torrent_hash) if torrent_hash else {}
        is_paused = torrent_info.get('paused', False)
        state = torrent_info.get('state', '').lower()
        
        # Pause/Resume actions
        if is_paused or 'paused' in state:
            resume_action = QAction("▶ Resume", self)
            resume_action.triggered.connect(self.resume_torrent)
            context_menu.addAction(resume_action)
        else:
            pause_action = QAction("⏸ Pause", self)
            pause_action.triggered.connect(self.pause_torrent)
            context_menu.addAction(pause_action)
        
        context_menu.addSeparator()
        
        # File management actions
        open_folder_action = QAction("📁 Open Download Folder", self)
        open_folder_action.triggered.connect(self.open_download_folder)
        context_menu.addAction(open_folder_action)
        
        copy_magnet_action = QAction("🔗 Copy Magnet Link", self)
        copy_magnet_action.triggered.connect(self.copy_magnet_link)
        context_menu.addAction(copy_magnet_action)
        
        context_menu.addSeparator()
        
        # Priority actions (submenu)
        priority_menu = context_menu.addMenu("⚡ Priority")
        
        high_priority_action = QAction("High", self)
        high_priority_action.triggered.connect(lambda: self.set_torrent_priority('high'))
        priority_menu.addAction(high_priority_action)
        
        normal_priority_action = QAction("Normal", self)
        normal_priority_action.triggered.connect(lambda: self.set_torrent_priority('normal'))
        priority_menu.addAction(normal_priority_action)
        
        low_priority_action = QAction("Low", self)
        low_priority_action.triggered.connect(lambda: self.set_torrent_priority('low'))
        priority_menu.addAction(low_priority_action)
        
        context_menu.addSeparator()
        
        # Remove actions
        remove_action = QAction("🗑 Remove Torrent", self)
        remove_action.triggered.connect(self.remove_torrent)
        context_menu.addAction(remove_action)
        
        remove_data_action = QAction("🗑💥 Remove Torrent + Data", self)
        remove_data_action.triggered.connect(self.remove_torrent_and_data)
        context_menu.addAction(remove_data_action)
        
        # Show the menu
        context_menu.exec_(self.torrent_list.mapToGlobal(position))
        
    def init_ui(self):
        self.setWindowTitle("PyTorrent - Torrent Client")
        self.setGeometry(100, 100, 1200, 800)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # Create torrent list
        self.torrent_list = QTreeWidget()
        self.torrent_list.setHeaderLabels([
            "Name", "Size", "Progress", "Download Speed", 
            "Upload Speed", "ETA", "Ratio", "Status"
        ])
        self.torrent_list.setRootIsDecorated(False)
        self.torrent_list.setAlternatingRowColors(True)
        self.torrent_list.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Enable custom context menu
        self.torrent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.torrent_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set custom delegate for progress bars
        self.progress_delegate = ProgressBarDelegate()
        self.torrent_list.setItemDelegateForColumn(2, self.progress_delegate)
        
        splitter.addWidget(self.torrent_list)
        
        # Create details panel
        details_frame = QFrame()
        details_layout = QVBoxLayout(details_frame)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(QLabel("Torrent Details:"))
        details_layout.addWidget(self.details_text)
        
        splitter.addWidget(details_frame)
        splitter.setSizes([600, 200])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        add_torrent_action = QAction("Add Torrent File...", self)
        add_torrent_action.setShortcut("Ctrl+O")
        add_torrent_action.triggered.connect(self.add_torrent_file)
        file_menu.addAction(add_torrent_action)
        
        add_magnet_action = QAction("Add Magnet Link...", self)
        add_magnet_action.setShortcut("Ctrl+M")
        add_magnet_action.triggered.connect(self.add_magnet_link)
        file_menu.addAction(add_magnet_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Torrent menu
        torrent_menu = menubar.addMenu("Torrent")
        
        self.pause_action = QAction("Pause", self)
        self.pause_action.triggered.connect(self.pause_torrent)
        self.pause_action.setEnabled(False)
        torrent_menu.addAction(self.pause_action)
        
        self.resume_action = QAction("Resume", self)
        self.resume_action.triggered.connect(self.resume_torrent)
        self.resume_action.setEnabled(False)
        torrent_menu.addAction(self.resume_action)
        
        self.remove_action = QAction("Remove", self)
        self.remove_action.triggered.connect(self.remove_torrent)
        self.remove_action.setEnabled(False)
        torrent_menu.addAction(self.remove_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        preferences_action = QAction("Preferences...", self)
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)
        
    def create_toolbar(self):
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add torrent button
        add_torrent_btn = QPushButton("Add Torrent")
        add_torrent_btn.clicked.connect(self.add_torrent_file)
        toolbar.addWidget(add_torrent_btn)
        
        # Add magnet button
        add_magnet_btn = QPushButton("Add Magnet")
        add_magnet_btn.clicked.connect(self.add_magnet_link)
        toolbar.addWidget(add_magnet_btn)
        
        toolbar.addSeparator()
        
        # Control buttons
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_torrent)
        self.pause_btn.setEnabled(False)
        toolbar.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("Resume")
        self.resume_btn.clicked.connect(self.resume_torrent)
        self.resume_btn.setEnabled(False)
        toolbar.addWidget(self.resume_btn)
        
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_torrent)
        self.remove_btn.setEnabled(False)
        toolbar.addWidget(self.remove_btn)
        
    def create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add download/upload speed indicators
        self.download_speed_label = QLabel("⬇ 0 KB/s")
        self.upload_speed_label = QLabel("⬆ 0 KB/s")
        
        self.status_bar.addPermanentWidget(self.download_speed_label)
        self.status_bar.addPermanentWidget(self.upload_speed_label)
        
    def setup_timer(self):
        """Setup timer for updating torrent information"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_torrents)
        self.update_timer.start(1000)  # Update every second
        
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to set an icon
        try:
            # Use a more appropriate icon from system
            icon = self.style().standardIcon(self.style().SP_DriveNetIcon)
            if icon.isNull():
                icon = self.style().standardIcon(self.style().SP_ComputerIcon)
            self.tray_icon.setIcon(icon)
        except Exception:
            # Fallback to a basic icon
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show/Hide action
        show_action = QAction("Show PyTorrent", self)
        show_action.triggered.connect(self.show_normal)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide to Tray", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # Add torrent actions
        add_torrent_action = QAction("Add Torrent File...", self)
        add_torrent_action.triggered.connect(self.add_torrent_file)
        tray_menu.addAction(add_torrent_action)
        
        add_magnet_action = QAction("Add Magnet Link...", self)
        add_magnet_action.triggered.connect(self.add_magnet_link)
        tray_menu.addAction(add_magnet_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_action)
        
        # Set the menu
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect double-click to show/hide
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Set tooltip
        self.update_tray_tooltip()
        
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show_normal()
                
    def show_normal(self):
        """Show and raise the window"""
        self.show()
        self.raise_()
        self.activateWindow()
        
    def update_tray_tooltip(self):
        """Update system tray tooltip with current stats"""
        if hasattr(self, 'tray_icon'):
            active_torrents = len(self.torrent_manager.torrent_handles)
            total_download = sum(info.get('download_rate', 0) 
                               for info in self.torrent_manager.get_all_torrent_info().values())
            total_upload = sum(info.get('upload_rate', 0) 
                             for info in self.torrent_manager.get_all_torrent_info().values())
            
            tooltip = f"PyTorrent - {active_torrents} torrents\n"
            tooltip += f"⬇ {self.format_speed(total_download)} | ⬆ {self.format_speed(total_upload)}"
            self.tray_icon.setToolTip(tooltip)
            
    def quit_application(self):
        """Properly quit the application"""
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        self.torrent_manager.shutdown()
        QApplication.quit()
        
    def add_torrent_file(self):
        """Add torrent from file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Torrent File", "", "Torrent files (*.torrent)"
        )
        if file_path:
            dialog = AddTorrentDialog(file_path, self)
            if dialog.exec_():
                download_path = dialog.get_download_path()
                selected_files = dialog.get_selected_files()
                self.torrent_manager.add_torrent_file(file_path, download_path, selected_files)
                
    def add_magnet_link(self):
        """Add torrent from magnet link"""
        magnet_link, ok = QInputDialog.getText(
            self, "Add Magnet Link", "Enter magnet link:"
        )
        if ok and magnet_link:
            dialog = AddTorrentDialog(magnet_link, self)
            if dialog.exec_():
                download_path = dialog.get_download_path()
                self.torrent_manager.add_magnet_link(magnet_link, download_path)
                
    def pause_torrent(self):
        """Pause selected torrent"""
        current_item = self.torrent_list.currentItem()
        if current_item:
            torrent_hash = current_item.data(0, Qt.UserRole)
            self.torrent_manager.pause_torrent(torrent_hash)
            
    def resume_torrent(self):
        """Resume selected torrent"""
        current_item = self.torrent_list.currentItem()
        if current_item:
            torrent_hash = current_item.data(0, Qt.UserRole)
            self.torrent_manager.resume_torrent(torrent_hash)
            
    def remove_torrent(self):
        """Remove selected torrent"""
        current_item = self.torrent_list.currentItem()
        if current_item:
            torrent_name = current_item.text(0)
            reply = QMessageBox.question(
                self, "Remove Torrent", 
                f"Are you sure you want to remove '{torrent_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                torrent_hash = current_item.data(0, Qt.UserRole)
                self.torrent_manager.remove_torrent(torrent_hash)
                
    def remove_torrent_and_data(self):
        """Remove selected torrent and delete files"""
        current_item = self.torrent_list.currentItem()
        if current_item:
            torrent_name = current_item.text(0)
            reply = QMessageBox.question(
                self, "Remove Torrent + Data", 
                f"Are you sure you want to remove '{torrent_name}' AND DELETE ALL FILES?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                torrent_hash = current_item.data(0, Qt.UserRole)
                self.torrent_manager.remove_torrent(torrent_hash, delete_files=True)
                
    def open_download_folder(self):
        """Open download folder for selected torrent"""
        current_item = self.torrent_list.currentItem()
        if current_item:
            torrent_hash = current_item.data(0, Qt.UserRole)
            torrent_info = self.torrent_manager.get_torrent_info(torrent_hash)
            if torrent_info and 'save_path' in torrent_info:
                import subprocess
                import platform
                
                save_path = torrent_info['save_path']
                try:
                    if platform.system() == 'Darwin':  # macOS
                        subprocess.run(['open', save_path])
                    elif platform.system() == 'Windows':
                        subprocess.run(['explorer', save_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', save_path])
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not open folder: {e}")
                    
    def copy_magnet_link(self):
        """Copy magnet link for selected torrent"""
        current_item = self.torrent_list.currentItem()
        if current_item:
            torrent_hash = current_item.data(0, Qt.UserRole)
            # For now, just show a placeholder message
            # In a real implementation, we'd need to store the original magnet link
            # or generate one from the torrent info
            QApplication.clipboard().setText(f"magnet:?xt=urn:btih:{torrent_hash}")
            self.status_bar.showMessage("Magnet link copied to clipboard", 2000)
            
    def set_torrent_priority(self, priority):
        """Set priority for selected torrent"""
        current_item = self.torrent_list.currentItem()
        if current_item:
            torrent_hash = current_item.data(0, Qt.UserRole)
            # This would need to be implemented in torrent_manager
            self.status_bar.showMessage(f"Priority set to {priority}", 2000)
                
    def show_preferences(self):
        """Show preferences dialog"""
        dialog = PreferencesDialog(self)
        if dialog.exec_():
            # Apply settings to torrent manager
            self.apply_preferences_to_manager()
            
    def apply_preferences_to_manager(self):
        """Apply settings from preferences to torrent manager"""
        settings = QSettings("PyTorrent", "PyTorrent")
        
        # Collect all settings into a dictionary
        settings_dict = {
            # Connection settings
            'port': settings.value("connection/port", 6881, type=int),
            'enable_dht': settings.value("connection/enable_dht", True, type=bool),
            'enable_lsd': settings.value("connection/enable_lsd", True, type=bool),
            'enable_upnp': settings.value("connection/upnp", True, type=bool),
            'enable_natpmp': settings.value("connection/upnp", True, type=bool),  # Use same setting as UPnP
            'max_connections': settings.value("connection/max_connections", 200, type=int),
            'max_uploads': settings.value("connection/max_uploads", 4, type=int),
            
            # Bandwidth settings
            'limit_download': settings.value("bandwidth/limit_download", False, type=bool),
            'download_limit': settings.value("bandwidth/download_limit", 1000, type=int),
            'limit_upload': settings.value("bandwidth/limit_upload", False, type=bool),
            'upload_limit': settings.value("bandwidth/upload_limit", 100, type=int),
        }
        
        # Apply to torrent manager
        self.torrent_manager.apply_session_settings(settings_dict)
        
        # Update default download path
        download_path = settings.value("downloads/default_path", 
                                     os.path.join(os.path.expanduser('~'), 'Downloads', 'PyTorrent'))
        self.torrent_manager.set_download_path(download_path)
        
    def on_selection_changed(self):
        """Handle torrent selection change"""
        current_item = self.torrent_list.currentItem()
        has_selection = current_item is not None
        
        # Enable/disable actions based on selection
        self.pause_action.setEnabled(has_selection)
        self.resume_action.setEnabled(has_selection)
        self.remove_action.setEnabled(has_selection)
        self.pause_btn.setEnabled(has_selection)
        self.resume_btn.setEnabled(has_selection)
        self.remove_btn.setEnabled(has_selection)
        
        # Update details panel
        if current_item:
            torrent_hash = current_item.data(0, Qt.UserRole)
            torrent_info = self.torrent_manager.get_torrent_info(torrent_hash)
            if torrent_info:
                self.update_details_panel(torrent_info)
        else:
            self.details_text.clear()
            
    def update_details_panel(self, torrent_info):
        """Update the details panel with torrent information"""
        details = f"""
Name: {torrent_info.get('name', 'N/A')}
Hash: {torrent_info.get('hash', 'N/A')}
Size: {self.format_size(torrent_info.get('total_size', 0))}
Downloaded: {self.format_size(torrent_info.get('downloaded', 0))}
Uploaded: {self.format_size(torrent_info.get('uploaded', 0))}
Ratio: {torrent_info.get('ratio', 0):.2f}
Peers: {torrent_info.get('num_peers', 0)}
Seeds: {torrent_info.get('num_seeds', 0)}
Save Path: {torrent_info.get('save_path', 'N/A')}
"""
        self.details_text.setPlainText(details.strip())
        
    def on_torrent_added(self, torrent_hash, torrent_info):
        """Handle torrent added signal"""
        item = QTreeWidgetItem()
        item.setData(0, Qt.UserRole, torrent_hash)
        self.update_torrent_item(item, torrent_info)
        self.torrent_list.addTopLevelItem(item)
        self.status_bar.showMessage(f"Added torrent: {torrent_info.get('name', 'Unknown')}")
        
    def on_torrent_updated(self, torrent_hash, torrent_info):
        """Handle torrent updated signal"""
        # Find the item with this hash
        for i in range(self.torrent_list.topLevelItemCount()):
            item = self.torrent_list.topLevelItem(i)
            if item.data(0, Qt.UserRole) == torrent_hash:
                self.update_torrent_item(item, torrent_info)
                break
                
        # Update details panel if this torrent is selected
        current_item = self.torrent_list.currentItem()
        if current_item and current_item.data(0, Qt.UserRole) == torrent_hash:
            self.update_details_panel(torrent_info)
            
    def on_torrent_removed(self, torrent_hash):
        """Handle torrent removed signal"""
        # Find and remove the item with this hash
        for i in range(self.torrent_list.topLevelItemCount()):
            item = self.torrent_list.topLevelItem(i)
            if item.data(0, Qt.UserRole) == torrent_hash:
                self.torrent_list.takeTopLevelItem(i)
                break
                
    def on_error_occurred(self, title, message):
        """Handle error signal from torrent manager"""
        QMessageBox.critical(self, title, message)
        self.status_bar.showMessage(f"Error: {message}", 5000)
        
    def on_torrent_completed(self, torrent_hash, torrent_info):
        """Handle torrent completion signal"""
        torrent_name = torrent_info.get('name', 'Unknown')
        size = self.format_size(torrent_info.get('total_size', 0))
        
        # Show system tray notification if available
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                "Download Complete! 🎉",
                f"{torrent_name}\nSize: {size}",
                QSystemTrayIcon.Information,
                5000
            )
        
        # Show status bar message
        self.status_bar.showMessage(f"✅ Completed: {torrent_name}", 10000)
        
        # Also show a non-blocking message box
        self.show_completion_toast(torrent_name, size)
        
    def show_completion_toast(self, torrent_name, size):
        """Show a non-blocking toast notification"""
        # Create a simple message dialog that auto-closes
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Download Complete! 🎉")
        msg.setText(f"<b>{torrent_name}</b><br>Size: {size}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.setDefaultButton(QMessageBox.Ok)
        
        # Make it non-modal so it doesn't block the UI
        msg.setWindowModality(Qt.NonModal)
        msg.show()
        
        # Auto-close after 5 seconds
        QTimer.singleShot(5000, msg.close)
                
    def update_torrent_item(self, item, torrent_info):
        """Update a torrent item in the list"""
        item.setText(0, torrent_info.get('name', 'Unknown'))
        item.setText(1, self.format_size(torrent_info.get('total_size', 0)))
        item.setText(2, f"{torrent_info.get('progress', 0):.1f}%")
        item.setText(3, f"{self.format_speed(torrent_info.get('download_rate', 0))}")
        item.setText(4, f"{self.format_speed(torrent_info.get('upload_rate', 0))}")
        item.setText(5, self.format_eta(torrent_info.get('eta', 0)))
        item.setText(6, f"{torrent_info.get('ratio', 0):.2f}")
        item.setText(7, torrent_info.get('state', 'Unknown'))
        
        # Store state in progress column for custom delegate
        item.setData(2, Qt.UserRole, torrent_info.get('state', 'Unknown'))
        
    def update_torrents(self):
        """Update all torrent information"""
        self.torrent_manager.update_torrents()
        
        # Update global download/upload speeds
        total_download = sum(info.get('download_rate', 0) 
                           for info in self.torrent_manager.get_all_torrent_info().values())
        total_upload = sum(info.get('upload_rate', 0) 
                         for info in self.torrent_manager.get_all_torrent_info().values())
        
        self.download_speed_label.setText(f"⬇ {self.format_speed(total_download)}")
        self.upload_speed_label.setText(f"⬆ {self.format_speed(total_upload)}")
        
        # Update tray tooltip
        self.update_tray_tooltip()
        
    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
        
    def format_speed(self, speed_bytes):
        """Format speed in human readable format"""
        return f"{self.format_size(speed_bytes)}/s"
        
    def format_eta(self, eta_seconds):
        """Format ETA in human readable format"""
        if eta_seconds <= 0:
            return "∞"
        
        if eta_seconds < 60:
            return f"{int(eta_seconds)}s"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
        elif eta_seconds < 86400:
            hours = int(eta_seconds // 3600)
            minutes = int((eta_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(eta_seconds // 86400)
            hours = int((eta_seconds % 86400) // 3600)
            return f"{days}d {hours}h"
            
    def closeEvent(self, event):
        """Handle application close"""
        # Check if system tray is available and user wants to minimize to tray
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            # For now, just minimize to tray on close
            # Later we can add a setting for this behavior
            self.hide()
            if not hasattr(self, '_showed_tray_message'):
                self.tray_icon.showMessage(
                    "PyTorrent",
                    "Application minimized to tray. Double-click the tray icon to restore.",
                    QSystemTrayIcon.Information,
                    3000
                )
                self._showed_tray_message = True
            event.ignore()
        else:
            # No system tray, actually exit
            self.torrent_manager.shutdown()
            event.accept()
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            # Check if any dropped files are torrent files
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.torrent'):
                        event.acceptProposedAction()
                        return
                    elif file_path.startswith('magnet:'):
                        event.acceptProposedAction()
                        return
        
        # Also accept text (for magnet links)
        if event.mimeData().hasText():
            text = event.mimeData().text().strip()
            if text.startswith('magnet:'):
                event.acceptProposedAction()
                return
                
        event.ignore()
        
    def dragMoveEvent(self, event):
        """Handle drag move events"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.torrent'):
                        # Process torrent file
                        self.process_dropped_torrent(file_path)
                        
        elif event.mimeData().hasText():
            text = event.mimeData().text().strip()
            if text.startswith('magnet:'):
                # Process magnet link
                self.process_dropped_magnet(text)
                
        event.acceptProposedAction()
        
    def process_dropped_torrent(self, file_path):
        """Process a dropped torrent file"""
        try:
            dialog = AddTorrentDialog(file_path, self)
            if dialog.exec_():
                download_path = dialog.get_download_path()
                selected_files = dialog.get_selected_files()
                self.torrent_manager.add_torrent_file(file_path, download_path, selected_files)
                self.status_bar.showMessage(f"Added torrent: {os.path.basename(file_path)}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add torrent: {str(e)}")
            
    def process_dropped_magnet(self, magnet_link):
        """Process a dropped magnet link"""
        try:
            dialog = AddTorrentDialog(magnet_link, self)
            if dialog.exec_():
                download_path = dialog.get_download_path()
                self.torrent_manager.add_magnet_link(magnet_link, download_path)
                self.status_bar.showMessage("Added magnet link", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add magnet link: {str(e)}") 