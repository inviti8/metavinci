#!/usr/bin/env python3
"""
Script to create version tags and trigger GitHub Actions builds
"""

import subprocess
import sys
import re
from pathlib import Path


def get_current_version():
    """Get current version from git tags"""
    try:
        result = subprocess.run(['git', 'tag', '--sort=-version:refname'], 
                              capture_output=True, text=True, check=True)
        tags = result.stdout.strip().split('\n')
        
        # Filter version tags
        version_tags = [tag for tag in tags if tag.startswith('v') and re.match(r'^v\d+\.\d+', tag)]
        
        if version_tags:
            return version_tags[0]  # Latest version
        else:
            return None
    except subprocess.CalledProcessError:
        return None


def suggest_next_version(current_version):
    """Suggest next version based on current version"""
    if not current_version:
        return "v0.01"
    
    # Extract version numbers
    match = re.match(r'^v(\d+)\.(\d+)(?:\.(\d+))?$', current_version)
    if not match:
        return "v0.01"
    
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3)) if match.group(3) else 0
    
    # Suggest patch increment
    return f"v{major}.{minor}.{patch + 1}"


def create_tag(version):
    """Create and push a version tag"""
    try:
        # Create the tag
        print(f"Creating tag: {version}")
        subprocess.run(['git', 'tag', version], check=True)
        
        # Push the tag
        print(f"Pushing tag: {version}")
        subprocess.run(['git', 'push', 'origin', version], check=True)
        
        print(f"✅ Successfully created and pushed tag: {version}")
        print(f"🚀 GitHub Actions build will start automatically!")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating tag: {e}")
        return False


def list_recent_tags():
    """List recent version tags"""
    try:
        result = subprocess.run(['git', 'tag', '--sort=-version:refname', '-l', 'v*'], 
                              capture_output=True, text=True, check=True)
        tags = result.stdout.strip().split('\n')
        
        if tags and tags[0]:
            print("Recent version tags:")
            for tag in tags[:10]:  # Show last 10 tags
                print(f"  {tag}")
        else:
            print("No version tags found")
            
    except subprocess.CalledProcessError as e:
        print(f"Error listing tags: {e}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python create_release.py <version>")
        print("   or: python create_release.py --suggest")
        print("   or: python create_release.py --list")
        print()
        print("Examples:")
        print("  python create_release.py v0.01")
        print("  python create_release.py v1.0.0")
        print("  python create_release.py --suggest")
        sys.exit(1)
    
    if sys.argv[1] == '--suggest':
        current_version = get_current_version()
        suggested_version = suggest_next_version(current_version)
        print(f"Current version: {current_version or 'None'}")
        print(f"Suggested next version: {suggested_version}")
        print()
        print("To create this version:")
        print(f"  python create_release.py {suggested_version}")
        return
    
    if sys.argv[1] == '--list':
        list_recent_tags()
        return
    
    version = sys.argv[1]
    
    # Validate version format
    if not re.match(r'^v\d+\.\d+(?:\.\d+)?$', version):
        print(f"❌ Invalid version format: {version}")
        print("Version should be in format: v0.01, v1.0.0, v2.1.3, etc.")
        sys.exit(1)
    
    # Check if tag already exists
    try:
        result = subprocess.run(['git', 'tag', '-l', version], 
                              capture_output=True, text=True, check=True)
        if result.stdout.strip():
            print(f"❌ Tag {version} already exists!")
            sys.exit(1)
    except subprocess.CalledProcessError:
        pass
    
    # Confirm before creating
    print(f"About to create tag: {version}")
    print("This will trigger GitHub Actions builds for all platforms.")
    response = input("Continue? (y/N): ")
    
    if response.lower() in ['y', 'yes']:
        create_tag(version)
    else:
        print("Cancelled.")


if __name__ == "__main__":
    main() 