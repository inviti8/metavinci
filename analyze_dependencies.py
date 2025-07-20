#!/usr/bin/env python3
"""
Script to analyze dependencies and their impact on executable size
"""

import subprocess
import sys
import os
from pathlib import Path


def get_package_size(package_name):
    """Get the size of a Python package"""
    try:
        result = subprocess.run([
            sys.executable, '-c', 
            f'import {package_name}; print(__import__({package_name}).__file__)'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            package_path = result.stdout.strip()
            if package_path and os.path.exists(package_path):
                # Get the directory size
                package_dir = Path(package_path).parent
                total_size = 0
                file_count = 0
                
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
                
                return total_size, file_count, package_dir
    except Exception as e:
        pass
    
    return 0, 0, None


def analyze_requirements():
    """Analyze all packages in requirements.txt"""
    print("Analyzing dependencies for size impact...")
    print("=" * 60)
    
    # Read requirements.txt
    requirements_file = Path('requirements.txt')
    if not requirements_file.exists():
        print("Error: requirements.txt not found")
        return
    
    packages = []
    with open(requirements_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (remove version specifiers)
                package_name = line.split('==')[0].split('>=')[0].split('<=')[0]
                packages.append(package_name)
    
    # Analyze each package
    total_size = 0
    package_sizes = []
    
    for package in packages:
        size, file_count, package_dir = get_package_size(package)
        if size > 0:
            size_mb = size / (1024 * 1024)
            total_size += size
            package_sizes.append((package, size_mb, file_count, package_dir))
            print(f"{package:20} {size_mb:8.2f} MB ({file_count:4d} files)")
    
    # Sort by size (largest first)
    package_sizes.sort(key=lambda x: x[1], reverse=True)
    
    print("\n" + "=" * 60)
    print("LARGEST PACKAGES (contributing to executable size):")
    print("=" * 60)
    
    for package, size_mb, file_count, package_dir in package_sizes[:10]:
        print(f"{package:20} {size_mb:8.2f} MB")
    
    total_mb = total_size / (1024 * 1024)
    print(f"\nTotal analyzed size: {total_mb:.2f} MB")
    
    # Provide recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    large_packages = [p for p, s, _, _ in package_sizes if s > 10]
    if large_packages:
        print("Large packages (>10MB) that significantly impact size:")
        for package in large_packages:
            print(f"  - {package}")
        print("\nConsider:")
        print("  - Using lighter alternatives")
        print("  - Excluding unused modules")
        print("  - Using --exclude-module in PyInstaller")
    
    # Check for common heavy packages
    heavy_packages = ['PyQt5', 'pillow', 'cryptography', 'pycryptodome']
    found_heavy = [p for p in heavy_packages if any(pkg == p for pkg, _, _, _ in package_sizes)]
    
    if found_heavy:
        print(f"\nHeavy packages found: {', '.join(found_heavy)}")
        print("These are common causes of large executable sizes.")


def analyze_executable_size(executable_path):
    """Analyze a built executable"""
    if not os.path.exists(executable_path):
        print(f"Error: Executable not found at {executable_path}")
        return
    
    size_bytes = os.path.getsize(executable_path)
    size_mb = size_bytes / (1024 * 1024)
    
    print(f"\nExecutable Analysis: {executable_path}")
    print(f"Size: {size_mb:.2f} MB ({size_bytes:,} bytes)")
    
    if size_mb > 50:
        print("⚠️  Very large executable - consider optimization")
    elif size_mb > 30:
        print("📦 Large executable - typical for GUI applications")
    elif size_mb > 15:
        print("📦 Moderate size - reasonable for complex applications")
    else:
        print("✅ Good size - well optimized")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python analyze_dependencies.py <command>")
        print("Commands:")
        print("  analyze    - Analyze all dependencies")
        print("  size <path> - Analyze executable size")
        return
    
    command = sys.argv[1]
    
    if command == "analyze":
        analyze_requirements()
    elif command == "size" and len(sys.argv) > 2:
        analyze_executable_size(sys.argv[2])
    else:
        print("Invalid command. Use 'analyze' or 'size <path>'.")


if __name__ == "__main__":
    main() 