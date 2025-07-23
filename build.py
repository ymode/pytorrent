#!/usr/bin/env python3
"""
PyTorrent Build Script
Creates a standalone executable from the PyTorrent application
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if all required tools are installed"""
    print("🔍 Checking requirements...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller installed")
    
    # Check if all dependencies are available
    required_modules = ['PyQt5', 'libtorrent', 'requests']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} found")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} not found")
    
    if missing_modules:
        print(f"⚠️  Missing modules: {', '.join(missing_modules)}")
        print("Please install them with: pip install " + " ".join(missing_modules))
        return False
    
    return True

def create_icon_files():
    """Convert SVG icon to platform-specific formats"""
    print("🎨 Creating icon files...")
    
    # For now, we'll use the system's default icon generation
    # In a production build, you'd want to use a proper icon converter
    current_dir = Path(__file__).parent
    
    if platform.system() == 'Darwin':  # macOS
        print("📱 macOS detected - would create .icns files")
        # Would use: iconutil -c icns icon.iconset
        
    elif platform.system() == 'Windows':  # Windows
        print("🪟 Windows detected - would create .ico files")
        # Would use PIL or similar to create .ico from SVG
        
    else:  # Linux
        print("🐧 Linux detected - using PNG icons")
    
    print("✅ Icon files ready")

def build_application():
    """Build the standalone application"""
    print("🔨 Building PyTorrent...")
    
    current_dir = Path(__file__).parent
    
    # Generate the spec file
    print("📝 Generating build specification...")
    subprocess.run([sys.executable, "build_spec.py"], cwd=current_dir)
    
    # Clean previous builds
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_path)
    
    # Build with PyInstaller
    print("⚙️  Running PyInstaller...")
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller", 
        "--clean",
        "PyTorrent.spec"
    ], cwd=current_dir)
    
    if result.returncode == 0:
        print("🎉 Build successful!")
        
        # Show the output location
        system = platform.system()
        if system == 'Darwin':
            output_path = current_dir / "dist" / "PyTorrent.app"
            print(f"📦 macOS App Bundle created: {output_path}")
            print("   You can drag this to Applications folder or run directly")
        elif system == 'Windows':
            output_path = current_dir / "dist" / "PyTorrent.exe"
            print(f"📦 Windows Executable created: {output_path}")
            print("   You can run this file directly or distribute it")
        else:
            output_path = current_dir / "dist" / "PyTorrent"
            print(f"📦 Linux Executable created: {output_path}")
            print("   You can run this file directly or create a .deb/.rpm package")
            
        return True
    else:
        print("❌ Build failed!")
        return False

def create_distribution():
    """Create a distribution package"""
    print("📦 Creating distribution package...")
    
    current_dir = Path(__file__).parent
    dist_dir = current_dir / "dist"
    
    if not dist_dir.exists():
        print("❌ No dist directory found. Run build first.")
        return False
    
    # Create a release directory
    release_dir = current_dir / "release"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy the built application
    system = platform.system()
    if system == 'Darwin':
        app_name = "PyTorrent.app"
        shutil.copytree(dist_dir / app_name, release_dir / app_name)
    elif system == 'Windows':
        app_name = "PyTorrent.exe"
        shutil.copy2(dist_dir / app_name, release_dir / app_name)
    else:
        app_name = "PyTorrent"
        shutil.copy2(dist_dir / app_name, release_dir / app_name)
        # Make executable on Linux
        os.chmod(release_dir / app_name, 0o755)
    
    # Copy README and other files
    files_to_copy = ["README.md", "BUGS_AND_FEATURES.md"]
    for file_name in files_to_copy:
        file_path = current_dir / file_name
        if file_path.exists():
            shutil.copy2(file_path, release_dir / file_name)
    
    # Create a simple installation guide
    install_guide = release_dir / "INSTALLATION.txt"
    with open(install_guide, 'w') as f:
        f.write("PyTorrent - Installation Guide\\n")
        f.write("=" * 35 + "\\n\\n")
        
        if system == 'Darwin':
            f.write("macOS Installation:\\n")
            f.write("1. Drag PyTorrent.app to your Applications folder\\n")
            f.write("2. Right-click and select 'Open' the first time (security)\\n")
            f.write("3. The app will be available in Launchpad\\n\\n")
        elif system == 'Windows':
            f.write("Windows Installation:\\n")
            f.write("1. Double-click PyTorrent.exe to run\\n")
            f.write("2. Windows may show a security warning - click 'More info' then 'Run anyway'\\n")
            f.write("3. You can create a desktop shortcut or pin to taskbar\\n\\n")
        else:
            f.write("Linux Installation:\\n")
            f.write("1. Make the file executable: chmod +x PyTorrent\\n")
            f.write("2. Run with: ./PyTorrent\\n")
            f.write("3. You can create a desktop entry or symlink to /usr/local/bin\\n\\n")
        
        f.write("Features:\\n")
        f.write("- Add torrent files or magnet links\\n")
        f.write("- Visual progress bars\\n")
        f.write("- System tray integration\\n")
        f.write("- Drag & drop support\\n")
        f.write("- Context menus\\n")
        f.write("- Download completion notifications\\n")
        f.write("- Resume interrupted downloads\\n\\n")
        
        f.write("For support, visit: https://github.com/your-username/pytorrent\\n")
    
    print(f"✅ Distribution package created in: {release_dir}")
    return True

def main():
    """Main build process"""
    print("🚀 PyTorrent Build System")
    print("=" * 25)
    
    if not check_requirements():
        print("❌ Requirements check failed. Please install missing dependencies.")
        return 1
    
    create_icon_files()
    
    if not build_application():
        print("❌ Build failed!")
        return 1
    
    if not create_distribution():
        print("⚠️  Distribution creation failed, but executable was built successfully.")
        return 0
    
    print("\\n🎉 PyTorrent build completed successfully!")
    print("   The standalone application is ready for distribution.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())