#!/usr/bin/env python3
"""
Deployment Helper Script for PythonAnywhere
This script helps prepare your project for deployment to PythonAnywhere
"""

import os
import shutil
import subprocess
import sys

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_step(step_num, description):
    print(f"\n{step_num}. {description}")

def check_file_exists(filepath):
    if os.path.exists(filepath):
        print(f"✓ {filepath} exists")
        return True
    else:
        print(f"✗ {filepath} missing")
        return False

def main():
    print_header("PythonAnywhere Deployment Preparation")
    
    print("This script will help you prepare your project for deployment to PythonAnywhere.")
    print("Make sure you have:")
    print("- A PythonAnywhere account")
    print("- All your project files in this directory")
    print("- Internet connection to upload files")
    
    input("\nPress Enter to continue...")
    
    # Check essential files
    print_header("Checking Project Files")
    
    essential_files = [
        'main.py',
        'requirements.txt',
        'wsgi.py',
        'templates/',
        'assets/',
        'voucher_parser.py',
        'invoice_generator.py'
    ]
    
    missing_files = []
    for file_path in essential_files:
        if not check_file_exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        print("Please ensure all required files are present before deployment.")
        return
    
    print("\n✓ All essential files are present!")
    
    # Check requirements
    print_header("Checking Dependencies")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read().strip().split('\n')
        
        print(f"Found {len(requirements)} dependencies:")
        for req in requirements:
            if req.strip():
                print(f"  - {req}")
    except Exception as e:
        print(f"Error reading requirements.txt: {e}")
    
    # Create deployment package
    print_header("Creating Deployment Package")
    
    deploy_dir = "deployment_package"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    
    os.makedirs(deploy_dir)
    
    # Copy essential files
    files_to_copy = [
        'main.py',
        'main_production.py',
        'wsgi.py',
        'requirements.txt',
        'voucher_parser.py',
        'invoice_generator.py',
        'README.md',
        'PYTHONANYWHERE_DEPLOYMENT.md'
    ]
    
    dirs_to_copy = [
        'templates',
        'assets'
    ]
    
    print("Copying files...")
    for file_path in files_to_copy:
        if os.path.exists(file_path):
            shutil.copy2(file_path, deploy_dir)
            print(f"  ✓ Copied {file_path}")
    
    print("Copying directories...")
    for dir_path in dirs_to_copy:
        if os.path.exists(dir_path):
            shutil.copytree(dir_path, os.path.join(deploy_dir, dir_path))
            print(f"  ✓ Copied {dir_path}/")
    
    # Create uploads and generated directories
    os.makedirs(os.path.join(deploy_dir, 'uploads'), exist_ok=True)
    os.makedirs(os.path.join(deploy_dir, 'generated'), exist_ok=True)
    
    print(f"\n✓ Deployment package created in '{deploy_dir}/'")
    
    # Final instructions
    print_header("Next Steps")
    print("1. Go to https://www.pythonanywhere.com and sign up/log in")
    print("2. In your dashboard, go to the 'Files' tab")
    print("3. Navigate to /home/yourusername/")
    print("4. Create a directory called 'UlendoInvoiceApp'")
    print("5. Upload all files from the 'deployment_package' folder")
    print("6. Follow the detailed instructions in PYTHONANYWHERE_DEPLOYMENT.md")
    
    print("\nImportant Notes:")
    print("- Free accounts have limited storage and processing power")
    print("- Some PDF libraries may not work on PythonAnywhere")
    print("- Consider upgrading to a paid plan for production use")
    print("- Your app will be available at: yourusername.pythonanywhere.com")
    
    print(f"\nDeployment package ready in: {os.path.abspath(deploy_dir)}")
    print("You can now upload these files to PythonAnywhere!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment preparation cancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Please check your project files and try again.")
