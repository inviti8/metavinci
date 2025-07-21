import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

def make_ico(png_path, out_path):
    sizes = [(16,16), (32,32), (48,48), (256,256)]
    img = Image.open(png_path)
    img.save(out_path, sizes=sizes)

def make_icns(png_path, out_path):
    try:
        from icnsutil import IcnsFile
    except ImportError:
        print("icnsutil is required. Install with: pip install icnsutil")
        sys.exit(1)
    img = Image.open(png_path)
    icns = IcnsFile()
    for size in [16, 32, 64, 128, 256, 512, 1024]:
        icon = img.resize((size, size), Image.LANCZOS)
        icns.add_icon(icon, size)
    with open(out_path, 'wb') as f:
        icns.write(f)

def main():
    png_path = Path('metavinci_desktop.png')
    ico_path = Path('metavinci_desktop.ico')
    icns_path = Path('metavinci_desktop.icns')

    if not png_path.exists():
        print(f"App icon PNG not found: {png_path}")
        sys.exit(1)

    if not ico_path.exists():
        print(f"Generating {ico_path}...")
        make_ico(png_path, ico_path)
    else:
        print(f"{ico_path} already exists.")

    if not icns_path.exists():
        print(f"Generating {icns_path}...")
        make_icns(png_path, icns_path)
    else:
        print(f"{icns_path} already exists.")

    print("Icon generation complete.")

if __name__ == '__main__':
    main() 