"""
Torrent Manager - Handles all torrent operations using libtorrent
"""

import os
import time
import threading
import pickle
import json
from PyQt5.QtCore import QObject, pyqtSignal
import libtorrent as lt

class TorrentManager(QObject):
    # Signals for GUI updates
    torrent_added = pyqtSignal(str, dict)  # hash, info
    torrent_updated = pyqtSignal(str, dict)  # hash, info
    torrent_removed = pyqtSignal(str)  # hash
    error_occurred = pyqtSignal(str, str)  # title, message
    torrent_completed = pyqtSignal(str, dict)  # hash, info
    
    def __init__(self):
        super().__init__()
        
        # Initialize libtorrent session
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        
        # Set session settings (compatible with both old and new libtorrent versions)
        try:
            # Try new API first (libtorrent 2.0+)
            settings = lt.settings_pack()
            settings['user_agent'] = 'PyTorrent/1.0.0'
            settings['enable_dht'] = True
            settings['enable_lsd'] = True
            settings['enable_upnp'] = True
            settings['enable_natpmp'] = True
            self.session.apply_settings(settings)
        except AttributeError:
            # Fall back to old API (libtorrent 1.x)
            settings = self.session.get_settings()
            settings['user_agent'] = 'PyTorrent/1.0.0'
            settings['enable_dht'] = True
            settings['enable_lsd'] = True
            settings['enable_upnp'] = True
            settings['enable_natpmp'] = True
            self.session.apply_settings(settings)
        
        # Start DHT
        self.session.start_dht()
        
        # Add DHT routers
        self.session.add_dht_router('router.bittorrent.com', 6881)
        self.session.add_dht_router('dht.transmissionbt.com', 6881)
        
        # Torrent handles storage
        self.torrent_handles = {}  # hash -> handle
        self.torrent_info_cache = {}  # hash -> info dict
        self.pending_file_priorities = {}  # hash -> selected_files (for magnets)
        self.completed_torrents = set()  # Track which torrents have already been marked complete
        
        # Default download directory
        self.default_download_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'PyTorrent')
        os.makedirs(self.default_download_path, exist_ok=True)
        
        # Resume data directory
        self.resume_data_path = os.path.join(os.path.expanduser('~'), '.pytorrent', 'resume_data')
        os.makedirs(self.resume_data_path, exist_ok=True)
        
        # Load existing torrents from resume data
        self.load_resume_data()
        
    def load_resume_data(self):
        """Load torrents from saved resume data"""
        try:
            session_file = os.path.join(self.resume_data_path, 'session.json')
            if not os.path.exists(session_file):
                return
                
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
            for torrent_data in session_data.get('torrents', []):
                try:
                    torrent_hash = torrent_data['hash']
                    resume_file = os.path.join(self.resume_data_path, f"{torrent_hash}.resume")
                    
                    if os.path.exists(resume_file):
                        # Create add_torrent_params
                        params = lt.add_torrent_params()
                        
                        # Load resume data
                        with open(resume_file, 'rb') as rf:
                            params.resume_data = rf.read()
                            
                        params.save_path = torrent_data.get('save_path', self.default_download_path)
                        
                        # Add torrent file if available
                        if 'torrent_file' in torrent_data and os.path.exists(torrent_data['torrent_file']):
                            params.ti = lt.torrent_info(torrent_data['torrent_file'])
                        elif 'magnet_link' in torrent_data:
                            # Parse magnet link
                            magnet_params = lt.parse_magnet_uri(torrent_data['magnet_link'])
                            params.info_hash = magnet_params.info_hash
                            params.name = magnet_params.name
                            
                        # Add to session
                        handle = self.session.add_torrent(params)
                        self.torrent_handles[torrent_hash] = handle
                        
                        # Get initial info and emit signal
                        info = self._get_torrent_status(handle)
                        self.torrent_info_cache[torrent_hash] = info
                        self.torrent_added.emit(torrent_hash, info)
                        
                except Exception as e:
                    print(f"Error loading torrent {torrent_data.get('hash', 'unknown')}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error loading resume data: {e}")
            
    def save_resume_data(self):
        """Save current session and resume data"""
        try:
            session_data = {'torrents': []}
            
            for torrent_hash, handle in self.torrent_handles.items():
                if not handle.is_valid():
                    continue
                    
                try:
                    # Request resume data
                    handle.save_resume_data()
                    
                    # Collect torrent info
                    torrent_data = {
                        'hash': torrent_hash,
                        'save_path': handle.save_path(),
                        'name': handle.name() if handle.has_metadata() else 'Unknown'
                    }
                    
                    # Store torrent file path if available
                    if handle.torrent_file():
                        torrent_file_path = os.path.join(self.resume_data_path, f"{torrent_hash}.torrent")
                        with open(torrent_file_path, 'wb') as f:
                            f.write(lt.bencode(handle.torrent_file().to_dict()))
                        torrent_data['torrent_file'] = torrent_file_path
                        
                    session_data['torrents'].append(torrent_data)
                    
                except Exception as e:
                    print(f"Error saving resume data for {torrent_hash}: {e}")
                    continue
            
            # Save session data
            session_file = os.path.join(self.resume_data_path, 'session.json')
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            # Wait for resume data to be generated
            time.sleep(1)
            
            # Save resume data files
            alerts = self.session.pop_alerts()
            for alert in alerts:
                if isinstance(alert, lt.save_resume_data_alert):
                    resume_file = os.path.join(self.resume_data_path, f"{str(alert.handle.info_hash())}.resume")
                    with open(resume_file, 'wb') as f:
                        f.write(lt.bencode(alert.resume_data))
                        
        except Exception as e:
            error_msg = f"Error saving resume data: {str(e)}"
            self.error_occurred.emit("Save Error", error_msg)
        
    def add_torrent_file(self, torrent_file_path, download_path=None, selected_files=None):
        """Add a torrent from file"""
        try:
            if download_path is None:
                download_path = self.default_download_path
                
            # Load torrent info
            torrent_info = lt.torrent_info(torrent_file_path)
            
            # Create add_torrent_params
            params = lt.add_torrent_params()
            params.ti = torrent_info
            params.save_path = download_path
            params.storage_mode = lt.storage_mode_t.storage_mode_sparse
            
            # Add torrent to session
            handle = self.session.add_torrent(params)
            torrent_hash = str(handle.info_hash())
            
            # Store handle
            self.torrent_handles[torrent_hash] = handle
            
            # Set file priorities if specified
            if selected_files is not None and handle.has_metadata():
                self.set_file_priorities(handle, selected_files)
            
            # Get initial info
            info = self._get_torrent_status(handle)
            self.torrent_info_cache[torrent_hash] = info
            
            # Emit signal
            self.torrent_added.emit(torrent_hash, info)
            
            # Save resume data for persistence
            self.save_resume_data()
            
            return torrent_hash
            
        except Exception as e:
            error_msg = f"Failed to add torrent file: {str(e)}"
            self.error_occurred.emit("Add Torrent Error", error_msg)
            return None
            
    def add_magnet_link(self, magnet_link, download_path=None, selected_files=None):
        """Add a torrent from magnet link"""
        try:
            if download_path is None:
                download_path = self.default_download_path
                
            # Parse magnet link
            params = lt.parse_magnet_uri(magnet_link)
            params.save_path = download_path
            params.storage_mode = lt.storage_mode_t.storage_mode_sparse
            
            # Add torrent to session
            handle = self.session.add_torrent(params)
            torrent_hash = str(handle.info_hash())
            
            # Store handle
            self.torrent_handles[torrent_hash] = handle
            
            # Store file priorities for when metadata becomes available
            if selected_files is not None:
                self.pending_file_priorities[torrent_hash] = selected_files
            
            # Get initial info
            info = self._get_torrent_status(handle)
            self.torrent_info_cache[torrent_hash] = info
            
            # Emit signal
            self.torrent_added.emit(torrent_hash, info)
            
            # Save resume data for persistence
            self.save_resume_data()
            
            return torrent_hash
            
        except Exception as e:
            error_msg = f"Failed to add magnet link: {str(e)}"
            self.error_occurred.emit("Add Magnet Error", error_msg)
            return None
            
    def pause_torrent(self, torrent_hash):
        """Pause a torrent"""
        if torrent_hash in self.torrent_handles:
            handle = self.torrent_handles[torrent_hash]
            handle.pause()
            
    def resume_torrent(self, torrent_hash):
        """Resume a torrent"""
        if torrent_hash in self.torrent_handles:
            handle = self.torrent_handles[torrent_hash]
            handle.resume()
            
    def remove_torrent(self, torrent_hash, delete_files=False):
        """Remove a torrent"""
        if torrent_hash in self.torrent_handles:
            handle = self.torrent_handles[torrent_hash]
            
            # Remove from session
            if delete_files:
                self.session.remove_torrent(handle, lt.session.delete_files)
            else:
                self.session.remove_torrent(handle)
                
            # Remove from our storage
            del self.torrent_handles[torrent_hash]
            if torrent_hash in self.torrent_info_cache:
                del self.torrent_info_cache[torrent_hash]
            if torrent_hash in self.pending_file_priorities:
                del self.pending_file_priorities[torrent_hash]
            if torrent_hash in self.completed_torrents:
                self.completed_torrents.remove(torrent_hash)
                
            # Emit signal
            self.torrent_removed.emit(torrent_hash)
            
            # Save resume data to reflect removal
            self.save_resume_data()
            
    def set_file_priorities(self, handle, selected_files):
        """Set file priorities based on selected files"""
        try:
            if not handle.has_metadata():
                return
                
            torrent_info = handle.torrent_file()
            if not torrent_info:
                return
                
            num_files = torrent_info.num_files()
            priorities = []
            
            for i in range(num_files):
                if selected_files is None or i in selected_files:
                    priorities.append(4)  # Normal priority
                else:
                    priorities.append(0)  # Don't download
                    
            handle.prioritize_files(priorities)
            
        except Exception as e:
            error_msg = f"Failed to set file priorities: {str(e)}"
            self.error_occurred.emit("File Priority Error", error_msg)
            
    def get_torrent_info(self, torrent_hash):
        """Get information about a specific torrent"""
        return self.torrent_info_cache.get(torrent_hash, {})
        
    def get_all_torrent_info(self):
        """Get information about all torrents"""
        return self.torrent_info_cache.copy()
        
    def update_torrents(self):
        """Update information for all torrents"""
        for torrent_hash, handle in self.torrent_handles.items():
            try:
                info = self._get_torrent_status(handle)
                
                # Check for pending file priorities (magnet links getting metadata)
                if torrent_hash in self.pending_file_priorities and handle.has_metadata():
                    selected_files = self.pending_file_priorities.pop(torrent_hash)
                    self.set_file_priorities(handle, selected_files)
                
                # Check for completion
                if (info.get('progress', 0) >= 100.0 and 
                    torrent_hash not in self.completed_torrents and
                    info.get('state', '').lower() in ['finished', 'seeding']):
                    self.completed_torrents.add(torrent_hash)
                    self.torrent_completed.emit(torrent_hash, info)
                
                # Check if info changed significantly
                old_info = self.torrent_info_cache.get(torrent_hash, {})
                if self._info_changed(old_info, info):
                    self.torrent_info_cache[torrent_hash] = info
                    self.torrent_updated.emit(torrent_hash, info)
                else:
                    # Still update cache even if no signal emitted
                    self.torrent_info_cache[torrent_hash] = info
                    
            except Exception as e:
                # Only emit error for critical failures, not routine update issues
                if "invalid handle" not in str(e).lower():
                    error_msg = f"Error updating torrent: {str(e)}"
                    self.error_occurred.emit("Update Error", error_msg)
                
    def _get_torrent_status(self, handle):
        """Get status information from a torrent handle"""
        try:
            status = handle.status()
            
            # Calculate progress
            progress = 0
            if status.total_wanted > 0:
                progress = (status.total_wanted_done / status.total_wanted) * 100
                
            # Calculate ETA
            eta = 0
            if status.download_rate > 0 and status.total_wanted > status.total_wanted_done:
                eta = (status.total_wanted - status.total_wanted_done) / status.download_rate
                
            # Get state string
            state_names = {
                lt.torrent_status.queued_for_checking: 'Queued',
                lt.torrent_status.checking_files: 'Checking',
                lt.torrent_status.downloading_metadata: 'Downloading metadata',
                lt.torrent_status.downloading: 'Downloading',
                lt.torrent_status.finished: 'Finished',
                lt.torrent_status.seeding: 'Seeding',
                lt.torrent_status.allocating: 'Allocating',
                lt.torrent_status.checking_resume_data: 'Checking resume data'
            }
            
            state = state_names.get(status.state, 'Unknown')
            if status.paused:
                state = 'Paused'
                
            # Get ratio
            ratio = 0
            if status.total_done > 0:
                ratio = status.all_time_upload / status.total_done
                
            return {
                'name': handle.name() if handle.has_metadata() else 'Loading...',
                'hash': str(handle.info_hash()),
                'total_size': status.total_wanted,
                'downloaded': status.total_wanted_done,
                'uploaded': status.all_time_upload,
                'download_rate': status.download_rate,
                'upload_rate': status.upload_rate,
                'progress': progress,
                'eta': eta,
                'ratio': ratio,
                'state': state,
                'num_peers': status.num_peers,
                'num_seeds': status.num_seeds,
                'save_path': handle.save_path(),
                'paused': status.paused
            }
            
        except Exception as e:
            # Return error state without emitting signal (called frequently)
            return {
                'name': 'Error',
                'hash': str(handle.info_hash()),
                'total_size': 0,
                'downloaded': 0,
                'uploaded': 0,
                'download_rate': 0,
                'upload_rate': 0,
                'progress': 0,
                'eta': 0,
                'ratio': 0,
                'state': 'Error',
                'num_peers': 0,
                'num_seeds': 0,
                'save_path': '',
                'paused': False
            }
            
    def _info_changed(self, old_info, new_info):
        """Check if torrent info has changed significantly"""
        if not old_info:
            return True
            
        # Check for significant changes
        significant_keys = ['progress', 'download_rate', 'upload_rate', 'state', 'num_peers']
        
        for key in significant_keys:
            old_val = old_info.get(key, 0)
            new_val = new_info.get(key, 0)
            
            # For numeric values, check if change is significant
            if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                if abs(old_val - new_val) > 0.1:  # Threshold for change
                    return True
            else:
                if old_val != new_val:
                    return True
                    
        return False
        
    def set_download_path(self, path):
        """Set default download path"""
        self.default_download_path = path
        os.makedirs(path, exist_ok=True)
        
    def apply_session_settings(self, settings_dict):
        """Apply new settings to the session"""
        try:
            # Connection settings
            if 'port' in settings_dict:
                self.session.listen_on(settings_dict['port'], settings_dict['port'] + 10)
            
            # Try new API first (libtorrent 2.0+)
            try:
                settings = lt.settings_pack()
                
                if 'enable_dht' in settings_dict:
                    settings['enable_dht'] = settings_dict['enable_dht']
                if 'enable_lsd' in settings_dict:
                    settings['enable_lsd'] = settings_dict['enable_lsd']
                if 'enable_upnp' in settings_dict:
                    settings['enable_upnp'] = settings_dict['enable_upnp']
                if 'enable_natpmp' in settings_dict:
                    settings['enable_natpmp'] = settings_dict['enable_natpmp']
                if 'max_connections' in settings_dict:
                    settings['connections_limit'] = settings_dict['max_connections']
                if 'max_uploads' in settings_dict:
                    settings['unchoke_slots_limit'] = settings_dict['max_uploads']
                    
                # Bandwidth settings
                if 'download_limit' in settings_dict and settings_dict.get('limit_download', False):
                    settings['download_rate_limit'] = settings_dict['download_limit'] * 1024  # Convert KB/s to B/s
                else:
                    settings['download_rate_limit'] = 0  # Unlimited
                    
                if 'upload_limit' in settings_dict and settings_dict.get('limit_upload', False):
                    settings['upload_rate_limit'] = settings_dict['upload_limit'] * 1024  # Convert KB/s to B/s
                else:
                    settings['upload_rate_limit'] = 0  # Unlimited
                    
                # Apply settings
                self.session.apply_settings(settings)
                
            except AttributeError:
                # Fall back to old API (libtorrent 1.x)
                settings = self.session.get_settings()
                
                if 'enable_dht' in settings_dict:
                    settings['enable_dht'] = settings_dict['enable_dht']
                if 'enable_lsd' in settings_dict:
                    settings['enable_lsd'] = settings_dict['enable_lsd']
                if 'enable_upnp' in settings_dict:
                    settings['enable_upnp'] = settings_dict['enable_upnp']
                if 'enable_natpmp' in settings_dict:
                    settings['enable_natpmp'] = settings_dict['enable_natpmp']
                if 'max_connections' in settings_dict:
                    settings['connections_limit'] = settings_dict['max_connections']
                if 'max_uploads' in settings_dict:
                    settings['unchoke_slots_limit'] = settings_dict['max_uploads']
                    
                # Bandwidth settings (old API uses different names)
                if 'download_limit' in settings_dict and settings_dict.get('limit_download', False):
                    settings['download_rate_limit'] = settings_dict['download_limit'] * 1024
                else:
                    settings['download_rate_limit'] = 0
                    
                if 'upload_limit' in settings_dict and settings_dict.get('limit_upload', False):
                    settings['upload_rate_limit'] = settings_dict['upload_limit'] * 1024
                else:
                    settings['upload_rate_limit'] = 0
                    
                # Apply settings using old API
                self.session.apply_settings(settings)
            
        except Exception as e:
            error_msg = f"Failed to apply settings: {str(e)}"
            self.error_occurred.emit("Settings Error", error_msg)
        
    def shutdown(self):
        """Shutdown the torrent manager"""
        try:
            # Save resume data before shutdown
            self.save_resume_data()
            
            # Pause all torrents
            for handle in self.torrent_handles.values():
                if handle.is_valid():
                    handle.pause()
            
            # Clear handles
            self.torrent_handles.clear()
            self.torrent_info_cache.clear()
            
        except Exception as e:
            error_msg = f"Error during shutdown: {str(e)}"
            self.error_occurred.emit("Shutdown Error", error_msg) 