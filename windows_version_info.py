# -*- coding: utf-8 -*-
"""
Windows Version Info Generator for PyInstaller

This script generates a version info file that PyInstaller uses to embed
Windows version metadata into the executable. This helps with:
- SmartScreen reputation building
- Professional appearance in file properties
- Better user trust
"""

import sys

# Version components - update these for each release
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 0
VERSION_BUILD = 0

# Company and product info
COMPANY_NAME = "HEAVYMETA"
PRODUCT_NAME = "Metavinci"
FILE_DESCRIPTION = "Metavinci Desktop Application"
INTERNAL_NAME = "metavinci"
ORIGINAL_FILENAME = "metavinci.exe"
COPYRIGHT = "Copyright (C) 2024-2026 HEAVYMETA. All rights reserved."

# Generate version string
VERSION_STRING = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}.{VERSION_BUILD}"

# Version info template for PyInstaller
VERSION_INFO_TEMPLATE = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    filevers=({VERSION_MAJOR}, {VERSION_MINOR}, {VERSION_PATCH}, {VERSION_BUILD}),
    prodvers=({VERSION_MAJOR}, {VERSION_MINOR}, {VERSION_PATCH}, {VERSION_BUILD}),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{COMPANY_NAME}'),
        StringStruct(u'FileDescription', u'{FILE_DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{VERSION_STRING}'),
        StringStruct(u'InternalName', u'{INTERNAL_NAME}'),
        StringStruct(u'LegalCopyright', u'{COPYRIGHT}'),
        StringStruct(u'OriginalFilename', u'{ORIGINAL_FILENAME}'),
        StringStruct(u'ProductName', u'{PRODUCT_NAME}'),
        StringStruct(u'ProductVersion', u'{VERSION_STRING}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''

def generate_version_file(output_path="version_info.txt", version_override=None):
    """
    Generate a version info file for PyInstaller.

    Args:
        output_path: Path to write the version info file
        version_override: Optional version string like "0.08" to override defaults
    """
    global VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, VERSION_BUILD, VERSION_STRING

    if version_override:
        # Parse version string like "v0.08" or "0.08" or "installers-v0.08"
        import re
        match = re.search(r'v?(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?', version_override)
        if match:
            VERSION_MAJOR = int(match.group(1))
            VERSION_MINOR = int(match.group(2))
            VERSION_PATCH = int(match.group(3)) if match.group(3) else 0
            VERSION_BUILD = int(match.group(4)) if match.group(4) else 0
            VERSION_STRING = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}.{VERSION_BUILD}"

    # Regenerate template with updated values
    content = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    filevers=({VERSION_MAJOR}, {VERSION_MINOR}, {VERSION_PATCH}, {VERSION_BUILD}),
    prodvers=({VERSION_MAJOR}, {VERSION_MINOR}, {VERSION_PATCH}, {VERSION_BUILD}),
    # Contains a bitmask that specifies the valid bits 'flags'
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x40004 - NT
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{COMPANY_NAME}'),
        StringStruct(u'FileDescription', u'{FILE_DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{VERSION_STRING}'),
        StringStruct(u'InternalName', u'{INTERNAL_NAME}'),
        StringStruct(u'LegalCopyright', u'{COPYRIGHT}'),
        StringStruct(u'OriginalFilename', u'{ORIGINAL_FILENAME}'),
        StringStruct(u'ProductName', u'{PRODUCT_NAME}'),
        StringStruct(u'ProductVersion', u'{VERSION_STRING}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Generated version info file: {output_path}")
    print(f"  Version: {VERSION_STRING}")
    print(f"  Product: {PRODUCT_NAME}")
    print(f"  Company: {COMPANY_NAME}")

    return output_path


if __name__ == "__main__":
    # Allow passing version as command line argument
    version = sys.argv[1] if len(sys.argv) > 1 else None
    generate_version_file(version_override=version)
