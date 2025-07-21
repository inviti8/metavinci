import os
import sys
from pathlib import Path
from io import BytesIO
import tempfile

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
    size_code_map = [
        (16, "icp4"),
        (32, "icp5"),
        (64, "icp6"),
        (128, "ic07"),
        (256, "ic08"),
        (512, "ic09"),
        (1024, "ic10"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        for size, code in size_code_map:
            icon = img.resize((size, size), Image.LANCZOS)
            tmp_png = Path(tmpdir) / f"icon_{size}x{size}.png"
            icon.save(tmp_png, format="PNG")
            icns.add_media(code, file=str(tmp_png))
        icns.write(str(out_path))

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