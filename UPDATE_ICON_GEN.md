# Icon Generation System Update Plan

## Overview
This document outlines the plan to enhance the icon generation system to properly support Linux theming while maintaining compatibility with Windows and macOS.

## Current State
- Icons are generated for Windows (`.ico`) and macOS (`.icns`)
- Linux uses a single 64x64 PNG from `/usr/share/pixmaps/`
- No proper theme integration
- Inconsistent icon naming

## Goals
1. Support Linux icon theming standards
2. Maintain backward compatibility
3. Single source of truth for all platform icons
4. Support for high-DPI displays

## Implementation Plan

### 1. Directory Structure Update
```
project_root/
├── icons/
│   ├── metavinci.svg          # Vector source (recommended)
│   ├── metavinci_512x512.png  # High-res source
│   └── theme/
│       └── hicolor/
│           ├── 16x16/
│           │   └── apps/
│           │       └── metavinci.png
│           ├── 32x32/
│           │   └── apps/
│           │       └── metavinci.png
│           └── ...
```

### 2. Update `generate_icons.py`

#### New Dependencies
- `Pillow` (already in use)
- `icnsutil` (already in use)
- `argparse` (Python standard library)

#### New Functions to Add

```python
def make_linux_theme_icons(png_path: Path, out_dir: Path):
    """Generate Linux theme icons in standard sizes."""
    sizes = [16, 22, 24, 32, 48, 64, 128, 256, 512]
    img = Image.open(png_path)
    
    for size in sizes:
        # Create size-specific directory
        size_dir = out_dir / 'hicolor' / f'{size}x{size}' / 'apps'
        size_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate and save icon
        icon = img.resize((size, size), Image.LANCZOS)
        icon.save(size_dir / 'metavinci.png')

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate application icons')
    parser.add_argument('--platform', choices=['all', 'windows', 'linux', 'macos'], 
                      default='all', help='Target platform')
    parser.add_argument('--output-dir', type=Path, default=Path('dist/icons'),
                      help='Output directory for generated icons')
    parser.add_argument('--source', type=Path, default=Path('icons/metavinci_512x512.png'),
                      help='Source image file (SVG or high-res PNG)')
    return parser.parse_args()
```

### 3. Update Build Process

#### Linux (`build_installers.py`)
```python
def build_linux_installer(version):
    # ... existing code ...
    
    # Generate theme icons
    linux_icons_dir = pkg_dir / 'usr' / 'share' / 'icons'
    linux_icons_dir.mkdir(parents=True, exist_ok=True)
    
    subprocess.run([
        sys.executable, 'generate_icons.py',
        '--platform', 'linux',
        '--output-dir', str(linux_icons_dir),
        '--source', 'icons/metavinci_512x512.png'
    ])
    
    # Update .desktop file
    with open(src_desktop, 'r') as f:
        desktop_content = f.read()
    desktop_content = desktop_content.replace(
        'Icon=/usr/share/pixmaps/metavinci.png',
        'Icon=metavinci'  # Use theme icon name
    )
    
    # ... rest of the build process ...
```

### 4. Icon Naming Standardization
- Use `metavinci` as the base name for all icons
- Follow [Freedesktop Icon Naming Specification](https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html)
- File structure:
  - Windows: `metavinci.ico`
  - macOS: `metavinci.icns`
  - Linux: `metavinci.png` in theme directories

### 5. Testing Plan

#### Test Cases
1. **Linux**
   - [ ] Icons appear correctly in GNOME/KDE/XFCE
   - [ ] Icons scale properly for different DPI settings
   - [ ] Fallback to pixmap if theme is not available

2. **Windows**
   - [ ] ICO file contains all required sizes
   - [ ] Application icon appears correctly in taskbar and window

3. **macOS**
   - [ ] ICNS file contains all required sizes
   - [ ] Icons appear correctly in Dock and About dialog

### 6. Rollback Plan
1. Keep backup of current icon files
2. Tag current version before changes
3. Document rollback procedure in README

## Timeline
1. Update icon generation script: 1 day
2. Update build process: 1 day
3. Testing across platforms: 2 days
4. Documentation updates: 0.5 day

## Future Improvements
1. Add SVG source support
2. Automate icon generation in CI/CD
3. Add dark/light theme variants
4. Generate appstream metadata

## References
- [Freedesktop Icon Theme Specification](https://specifications.freedesktop.org/icon-theme-spec/icon-theme-spec-latest.html)
- [GNOME Icon Design Guidelines](https://developer.gnome.org/hig/guidelines/icons.html)
- [KDE Icon Design Guidelines](https://develop.kde.org/hig/style/icons/)
