import os
import shutil
import subprocess
from pathlib import Path
import argparse
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("--test", help="copy executable to local install directory", action="store_true")
parser.add_argument("--deb", help="create and execute debian build with fpm", action="store_true")
parser.add_argument("--mac", help="copy executable to mac local install directory", action="store_true")
args = parser.parse_args()

# get current working directory
cwd = Path.cwd()

# source files
src_file1 = cwd / 'metavinci.py'
src_file2 = cwd / 'requirements.txt'
ico_file = cwd / 'hvym_logo_64.ico'

# target directories for the build folder and files
build_dir = cwd / 'build' 
img_dir = cwd / 'images'
img_copied_dir = build_dir / 'images'
dist_dir = build_dir / 'dist' / 'linux'

if args.mac:
    dist_dir = build_dir / 'dist' / 'mac'
#src directories for fpm debian build
icon_src = img_dir  / 'metavinci.png'
build_src = build_dir / 'metavinci'
desktop_src = cwd / 'service' /'metavinci.desktop'

# target directories for fpm debian build
pkg_dir = cwd / 'package'
opt_dir = pkg_dir  / 'opt'
usr_dir = pkg_dir / 'usr'
share_dir = usr_dir / 'share'
apps_dir = share_dir / 'applications'
icons_dir = share_dir / 'icons'
hicolor_dir = icons_dir / 'hicolor'
desktop_target = apps_dir / 'metavinci.desktop'
build_target = opt_dir / 'metavinci'
dir_512 = hicolor_dir / '512x512' / 'apps'
icon_512 = dir_512  /  'metavinci.png'
dir_256 = hicolor_dir / '256x256' / 'apps'
icon_256 = dir_256  /  'metavinci.png'
dir_192 = hicolor_dir / '192x192' / 'apps'
icon_192 = dir_192  /  'metavinci.png'
dir_128 = hicolor_dir / '128x128' / 'apps'
icon_128 = dir_128  /  'metavinci.png'
dir_96 = hicolor_dir / '96x96' / 'apps'
icon_96 = dir_96  /  'metavinci.png'
dir_72 = hicolor_dir / '72x72' / 'apps'
icon_72 = dir_72  /  'metavinci.png'
dir_64 = hicolor_dir / '64x64' / 'apps'
icon_64 = dir_64  /  'metavinci.png'
dir_48 = hicolor_dir / '48x48' / 'apps'
icon_48 = dir_48  /  'metavinci.png'
dir_36 = hicolor_dir / '36x36' / 'apps' 
icon_36 = dir_36 /  'metavinci.png'
dir_32 = hicolor_dir / '32x32' / 'apps'
icon_32 = dir_32  /  'metavinci.png'
dir_24 = hicolor_dir / '24x24' / 'apps'
icon_24 = dir_24  /  'metavinci.png'
dir_22 = hicolor_dir / '22x22' / 'apps'
icon_22 = dir_22  /  'metavinci.png'
dir_16 = hicolor_dir / '16x16' / 'apps'
icon_16 = dir_16  /  'metavinci.png'

icon_sizes = [16, 22, 24, 32, 36, 48, 64, 72, 96, 128, 192, 256, 512]
icons_dirs = [dir_16, dir_22, dir_24, dir_32, dir_36, dir_48, dir_64, dir_72, dir_96, dir_128, dir_192, dir_256, dir_512]
icons = [icon_16, icon_22, icon_24, icon_32, icon_36, icon_48, icon_64, icon_72, icon_96, icon_128, icon_192, icon_256, icon_512]



# check if build dir exists, if not create it
if not build_dir.exists():
    build_dir.mkdir()
else: # delete all files inside the directory
    for item in build_dir.iterdir():
        if item.name != '.git' and item.name != 'README.md' and item.name != 'install.sh':
            if item.is_file():
                item.unlink()
            else:
                shutil.rmtree(item)

# copy source files to build directory
shutil.copy(src_file1, build_dir)
shutil.copy(src_file2, build_dir)
shutil.copytree(img_dir, build_dir / img_dir.name)

# install dependencies from requirements.txt
subprocess.run(['pip', 'install', '-r', str(build_dir / src_file2.name)], check=True)

# build the python script into an executable using PyInstaller
subprocess.run(['pyinstaller', '--noconsole', '--onefile', f'--icon={str(ico_file)}', f'--distpath={dist_dir}', '--add-data', 'images:images', '--add-data', 'data:data', '--add-data', 'service:service',  str(build_dir / src_file1.name)], check=True)

if args.deb:
    #check if packe dirs exist, if not create them
    if not pkg_dir.exists():
        pkg_dir.mkdir()

    if not opt_dir.exists():
        opt_dir.mkdir()

    if not usr_dir.exists():
        usr_dir.mkdir()

    if not share_dir.exists():
        share_dir.mkdir()

    if not apps_dir.exists():
        apps_dir.mkdir()

    if not icons_dir.exists():
        icons_dir.mkdir()

    if not hicolor_dir.exists():
        hicolor_dir.mkdir()

    for num in icon_sizes:
        path = os.path.join(str(hicolor_dir), f'{num}x{num}')
        if not os.path.isdir(path):
            os.makedirs(path)

    for dir in icons_dirs:
        if not dir.exists():
            dir.mkdir()

    #clean old icons
    for icon in icons:
        if icon.exists():
            icon.unlink()
    #clean old desktop file
    if desktop_target.exists():
        desktop_target.unlink()
    #clean the build directory
    if build_target.exists():
        shutil.rmtree(str(build_target))

    idx=0
    #resize and add new icons
    for num in icon_sizes:
        size = num, num
        infile = str(icon_src)
        outfile = str(icons[idx])
        im = Image.open(infile)
        im.thumbnail(size, Image.Resampling.LANCZOS)
        im.save(outfile)
        idx+=1

    #create new desktop file
    shutil.copy(str(desktop_src), str(apps_dir))
    #copy the build over
    shutil.copytree(str(build_src), str(build_target))

    # Change permissions for files in metavinci dir to 644
    for root, dirs, files in os.walk(str(build_target)):
        for file in files:
            file_path = os.path.join(root, file)
            os.chmod(file_path, 0o664)

    # Change permissions for directories in metavinci dir to 755
    for root, dirs, files in os.walk(str(build_target)):
        for directory in dirs:
            directory_path = os.path.join(root, directory)
            os.chmod(directory_path, 0o755)

    # Change permissions for files in share dir to 644
    for root, dirs, files in os.walk(str(share_dir)):
        for file in files:
            file_path = os.path.join(root, file)
            os.chmod(file_path, 0o664)

    # Make metavinci executable
    #os.chmod(os.path.join(str(build_src), 'metavinci'), 0o744)

# copy built executable to destination directory
# if args.test:
#     test_dir = Path('/home/desktop/.metavinci/bin/metavinci')
#     shutil.copy(str(dist_dir / (src_file1.stem )), test_dir)
#     bin_dir = Path('/home/desktop/.metavinci/bin/')
#     subprocess.Popen('chmod +x ./metavinci', cwd=bin_dir, shell=True, stderr=subprocess.STDOUT)
