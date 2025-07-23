"""
Add Torrent Dialog - Dialog for adding new torrents
"""

import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QCheckBox,
                             QTreeWidget, QTreeWidgetItem, QDialogButtonBox,
                             QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt
import libtorrent as lt

class AddTorrentDialog(QDialog):
    def __init__(self, torrent_path_or_magnet, parent=None):
        super().__init__(parent)
        self.torrent_path_or_magnet = torrent_path_or_magnet
        self.is_magnet = torrent_path_or_magnet.startswith('magnet:')
        self.torrent_info = None
        
        self.init_ui()
        self.load_torrent_info()
        
    def init_ui(self):
        self.setWindowTitle("Add Torrent")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Torrent info group
        info_group = QGroupBox("Torrent Information")
        info_layout = QFormLayout(info_group)
        
        self.name_label = QLabel("Loading...")
        self.size_label = QLabel("Loading...")
        self.files_label = QLabel("Loading...")
        
        info_layout.addRow("Name:", self.name_label)
        info_layout.addRow("Size:", self.size_label)
        info_layout.addRow("Files:", self.files_label)
        
        layout.addWidget(info_group)
        
        # Download path group
        path_group = QGroupBox("Download Options")
        path_layout = QFormLayout(path_group)
        
        # Download path
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setText(os.path.join(os.path.expanduser('~'), 'Downloads', 'PyTorrent'))
        path_browse_btn = QPushButton("Browse...")
        path_browse_btn.clicked.connect(self.browse_download_path)
        
        path_row.addWidget(self.path_edit)
        path_row.addWidget(path_browse_btn)
        
        path_layout.addRow("Save to:", path_row)
        
        # Start immediately checkbox
        self.start_immediately_cb = QCheckBox("Start download immediately")
        self.start_immediately_cb.setChecked(True)
        path_layout.addRow(self.start_immediately_cb)
        
        layout.addWidget(path_group)
        
        # File list (for multi-file torrents)
        self.files_group = QGroupBox("Files")
        files_layout = QVBoxLayout(self.files_group)
        
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["File", "Size"])
        self.files_tree.setRootIsDecorated(True)
        files_layout.addWidget(self.files_tree)
        
        # Select all/none buttons
        select_buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self.select_all_files)
        select_none_btn = QPushButton("Select None")
        select_none_btn.clicked.connect(self.select_no_files)
        
        select_buttons_layout.addWidget(select_all_btn)
        select_buttons_layout.addWidget(select_none_btn)
        select_buttons_layout.addStretch()
        
        files_layout.addLayout(select_buttons_layout)
        
        layout.addWidget(self.files_group)
        self.files_group.setVisible(False)  # Hidden until we load file info
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def load_torrent_info(self):
        """Load torrent information"""
        try:
            if self.is_magnet:
                # For magnet links, we can't get detailed info without starting the download
                self.name_label.setText("Magnet Link")
                self.size_label.setText("Unknown (will be determined after metadata download)")
                self.files_label.setText("Unknown")
            else:
                # Load from torrent file
                self.torrent_info = lt.torrent_info(self.torrent_path_or_magnet)
                
                # Update labels
                self.name_label.setText(self.torrent_info.name())
                self.size_label.setText(self.format_size(self.torrent_info.total_size()))
                self.files_label.setText(f"{self.torrent_info.num_files()} files")
                
                # Load file list if multi-file torrent
                if self.torrent_info.num_files() > 1:
                    self.load_file_list()
                    self.files_group.setVisible(True)
                    
        except Exception as e:
            self.name_label.setText("Error loading torrent")
            self.size_label.setText(str(e))
            self.files_label.setText("0 files")
            
    def load_file_list(self):
        """Load file list for multi-file torrents"""
        if not self.torrent_info:
            return
            
        self.files_tree.clear()
        
        # Group files by directory
        file_structure = {}
        
        for i in range(self.torrent_info.num_files()):
            file_info = self.torrent_info.file_at(i)
            file_path = file_info.path
            file_size = file_info.size
            
            # Split path into components
            path_parts = file_path.split('/')
            
            # Build directory structure
            current_dict = file_structure
            for part in path_parts[:-1]:  # All but the filename
                if part not in current_dict:
                    current_dict[part] = {}
                current_dict = current_dict[part]
                
            # Add file
            filename = path_parts[-1]
            current_dict[filename] = {
                'size': file_size,
                'index': i,
                'is_file': True
            }
            
        # Populate tree widget
        self.populate_file_tree(self.files_tree.invisibleRootItem(), file_structure)
        
        # Expand all items
        self.files_tree.expandAll()
        
    def populate_file_tree(self, parent_item, structure):
        """Recursively populate the file tree"""
        for name, content in structure.items():
            item = QTreeWidgetItem(parent_item)
            item.setText(0, name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked)
            
            if isinstance(content, dict) and content.get('is_file', False):
                # This is a file
                item.setText(1, self.format_size(content['size']))
                item.setData(0, Qt.UserRole, content['index'])
            else:
                # This is a directory
                item.setText(1, "")
                self.populate_file_tree(item, content)
                
    def browse_download_path(self):
        """Browse for download directory"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Download Directory", self.path_edit.text()
        )
        if path:
            self.path_edit.setText(path)
            
    def select_all_files(self):
        """Select all files in the tree"""
        self.set_all_files_checked(Qt.Checked)
        
    def select_no_files(self):
        """Deselect all files in the tree"""
        self.set_all_files_checked(Qt.Unchecked)
        
    def set_all_files_checked(self, state):
        """Set check state for all files"""
        def set_item_checked(item, state):
            item.setCheckState(0, state)
            for i in range(item.childCount()):
                set_item_checked(item.child(i), state)
                
        root = self.files_tree.invisibleRootItem()
        for i in range(root.childCount()):
            set_item_checked(root.child(i), state)
            
    def get_download_path(self):
        """Get the selected download path"""
        return self.path_edit.text()
        
    def get_start_immediately(self):
        """Get whether to start download immediately"""
        return self.start_immediately_cb.isChecked()
        
    def get_selected_files(self):
        """Get list of selected file indices"""
        if not self.files_group.isVisible():
            return None  # Single file or magnet, download all
            
        selected_files = []
        
        def check_item(item):
            if item.checkState(0) == Qt.Checked:
                file_index = item.data(0, Qt.UserRole)
                if file_index is not None:  # This is a file, not a directory
                    selected_files.append(file_index)
                    
            for i in range(item.childCount()):
                check_item(item.child(i))
                
        root = self.files_tree.invisibleRootItem()
        for i in range(root.childCount()):
            check_item(root.child(i))
            
        return selected_files
        
    def format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
            
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB" 