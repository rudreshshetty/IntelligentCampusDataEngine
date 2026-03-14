#!/usr/bin/env python3
"""
Sapthagiri NPS University - Logo Setup Helper
This script helps you save the Sapthagiri NPS University logo to the correct location
"""

import os
import shutil
from pathlib import Path

def setup_logo():
    print("\n" + "="*70)
    print("SAPTHAGIRI NPS UNIVERSITY - LOGO SETUP HELPER")
    print("="*70 + "\n")
    
    # Create logos directory
    logos_dir = os.path.join('static', 'logos')
    os.makedirs(logos_dir, exist_ok=True)
    print(f"✓ Logos directory ready: {logos_dir}\n")
    
    # Show current status
    logo_path = os.path.join(logos_dir, 'sapthagiri_logo.png')
    if os.path.exists(logo_path):
        file_size = os.path.getsize(logo_path)
        print(f"Current logo file: {logo_path}")
        print(f"File size: {file_size} bytes\n")
    
    # Provide instructions
    print("NEXT STEPS:")
    print("-" * 70)
    print("\n1. Your Sapthagiri NPS University logo image is ready to be saved")
    print(f"\n2. Save your logo to this exact location:")
    print(f"   {os.path.abspath(logo_path)}\n")
    print("3. Make sure the filename is EXACTLY: sapthagiri_logo.png\n")
    print("4. Quick save method:")
    print("   - Copy your logo image")
    print("   - Open Windows Explorer")
    print(f"   - Navigate to: {os.path.abspath(logos_dir)}")
    print("   - Paste the logo there")
    print("   - Rename to: sapthagiri_logo.png\n")
    print("5. Once saved, run the Flask app:")
    print("   python app.py\n")
    print("6. Open your browser:")
    print("   http://localhost:5000\n")
    print("7. Logo will appear on:")
    print("   - Login page (large, centered)")
    print("   - Student dashboard (sidebar)")
    print("   - Lecturer dashboard (sidebar)")
    print("   - Admin dashboard (sidebar)\n")
    
    print("="*70)
    print("FINAL CHECKLIST:")
    print("="*70)
    print("☐ Logo image file saved to: static/logos/")
    print("☐ Filename is EXACTLY: sapthagiri_logo.png")
    print("☐ Flask app started: python app.py")
    print("☐ Browser opened: http://localhost:5000")
    print("☐ Logo visible on all pages")
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    setup_logo()
    input("Press Enter to continue...")
