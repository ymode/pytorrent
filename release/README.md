# PyTorrent - Python Qt5 Torrent Client

A modern, full-featured BitTorrent client built with Python and Qt5, providing a clean and intuitive interface for downloading and managing torrents.

![PyTorrent](https://img.shields.io/badge/Python-3.7+-blue.svg)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

### Core Functionality
- ✅ **Torrent File Support** - Add torrents from `.torrent` files
- ✅ **Magnet Links** - Support for magnet links
- ✅ **Multi-file Torrents** - Handle torrents with multiple files
- ✅ **Selective Downloads** - Choose which files to download
- ✅ **Pause/Resume** - Control individual torrent downloads
- ✅ **Real-time Progress** - Live download/upload statistics

### Advanced Features
- 🌐 **DHT Support** - Distributed Hash Table for peer discovery
- 🔗 **UPnP/NAT-PMP** - Automatic port forwarding
- 📊 **Bandwidth Control** - Upload/download rate limiting
- 💾 **Resume Support** - Continue downloads after restart
- 🎯 **Smart Seeding** - Intelligent upload management

### User Interface
- 🎨 **Modern GUI** - Clean, intuitive Qt5 interface
- 📈 **Real-time Stats** - Download/upload speeds, ETA, ratio
- 📁 **File Management** - Organized download directory structure
- ⚙️ **Comprehensive Settings** - Detailed configuration options
- 📋 **Torrent Details** - Complete information panel

## Installation

### Prerequisites

Make sure you have Python 3.7 or higher installed on your system.

### Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### Manual Installation

If you prefer to install dependencies manually:

```bash
pip install PyQt5==5.15.10
pip install python-libtorrent==2.0.9
pip install requests==2.31.0
pip install bencode.py==4.0.0
```

## Usage

### Starting the Application

```bash
python main.py
```

### Adding Torrents

#### From Torrent File
1. Click **"Add Torrent"** button or use `Ctrl+O`
2. Select your `.torrent` file
3. Choose download directory
4. Select files to download (for multi-file torrents)
5. Click **OK** to start downloading

#### From Magnet Link
1. Click **"Add Magnet"** button or use `Ctrl+M`
2. Paste the magnet link
3. Choose download directory
4. Click **OK** to start downloading

### Managing Downloads

- **Pause/Resume**: Select a torrent and click the respective buttons
- **Remove**: Select a torrent and click **"Remove"** (files are preserved)
- **View Details**: Select a torrent to see detailed information
- **Progress Tracking**: Monitor download progress, speeds, and ETA

### Configuration

Access preferences via **Tools → Preferences** to configure:

#### General Settings
- Startup behavior
- Interface preferences
- Confirmation dialogs

#### Download Settings
- Default download directory
- Completed files handling
- Auto-management options

#### Connection Settings
- Listening port configuration
- DHT and peer discovery
- Connection limits

#### Bandwidth Settings
- Upload/download rate limits
- Alternative rate limiting
- Traffic shaping

## File Structure

```
PyTorrent/
├── main.py                 # Application entry point
├── torrent_client.py       # Main window and UI
├── torrent_manager.py      # Core torrent functionality
├── add_torrent_dialog.py   # Add torrent dialog
├── preferences_dialog.py   # Settings configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technical Details

### Dependencies
- **PyQt5**: Modern cross-platform GUI framework
- **python-libtorrent**: BitTorrent protocol implementation
- **requests**: HTTP library for web requests
- **bencode.py**: Bencode encoding/decoding

### Architecture
- **MVC Pattern**: Clean separation of concerns
- **Signal-Slot System**: Qt's event handling mechanism
- **Threading**: Non-blocking UI with background operations
- **Settings Persistence**: QSettings for configuration storage

### Supported Platforms
- Windows 10+
- macOS 10.14+
- Linux (Ubuntu 18.04+, Fedora 30+, etc.)

## Troubleshooting

### Common Issues

#### Import Error: No module named 'libtorrent'
```bash
# Try alternative installation
pip install python-libtorrent-binary
```

#### Permission Denied on Download Directory
- Ensure write permissions to download directory
- Choose a different download location
- Run with appropriate user permissions

#### Firewall/Network Issues
- Configure firewall to allow the application
- Enable UPnP in preferences
- Check router port forwarding settings

#### Poor Download Speeds
- Adjust connection limits in preferences
- Enable DHT and Local Service Discovery
- Check bandwidth limits settings

### Debug Mode

Run with debug output:
```bash
python main.py --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **libtorrent** team for the excellent BitTorrent library
- **Qt/PyQt** developers for the robust GUI framework
- BitTorrent community for protocol development and standards

## Roadmap

### Planned Features
- [ ] RSS feed support for automatic downloads
- [ ] Plugin system for extensibility
- [ ] Web interface for remote management
- [ ] Advanced filtering and search
- [ ] Integrated torrent search
- [ ] Scheduler for bandwidth management
- [ ] Encryption support
- [ ] IPFilter/blocklist support

---

**Note**: This is educational software. Please respect copyright laws and only download content you have permission to access. 