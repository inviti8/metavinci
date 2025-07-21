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
    # Try to use 'metavinci_desktop.png' as the source, else fallback to 'hvym_logo_64.png'
    png_candidates = [Path('metavinci_desktop.png'), Path('hvym_logo_64.png')]
    png_path = None
    for candidate in png_candidates:
        if candidate.exists():
            png_path = candidate
            break
    if not png_path:
        print("App icon PNG not found: metavinci_desktop.png or hvym_logo_64.png")
        sys.exit(1)

    # List of icon outputs to generate (name, function)
    icon_targets = [
        (Path('hvym_logo_64.ico'), make_ico),
        (Path('hvym_logo_64.icns'), make_icns),
        (Path('hvym_logo_64.png'), lambda src, out: Image.open(src).save(out)),
        (Path('metavinci_desktop.ico'), make_ico),
        (Path('metavinci_desktop.icns'), make_icns),
        (Path('metavinci_desktop.png'), lambda src, out: Image.open(src).save(out)),
    ]

    for out_path, func in icon_targets:
        if not out_path.exists():
            print(f"Generating {out_path}...")
            func(png_path, out_path)
        else:
            print(f"{out_path} already exists.")

    print("Icon generation complete.")

if __name__ == '__main__':
    main() 