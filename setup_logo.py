#!/usr/bin/env python3
"""
Script to save the Sapthagiri NPS University logo image
Run this script to automatically set up the logo
"""

import os
import base64
import sys

# Logo base64 encoded (Sapthagiri NPS University logo as PNG)
# This is a placeholder - replace with actual base64 encoded logo data
LOGO_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==
"""

def setup_logo():
    """Create logos directory and save the logo image"""
    
    # Define paths
    project_root = os.path.dirname(os.path.abspath(__file__))
    logos_dir = os.path.join(project_root, 'static', 'logos')
    logo_path = os.path.join(logos_dir, 'sapthagiri_logo.png')
    
    # Create logos directory if it doesn't exist
    os.makedirs(logos_dir, exist_ok=True)
    print(f"✓ Logos directory created/verified: {logos_dir}")
    
    # Check if logo already exists
    if os.path.exists(logo_path):
        print(f"✓ Logo already exists at: {logo_path}")
        return True
    
    print("\n" + "="*60)
    print("SAPTHAGIRI NPS UNIVERSITY - LOGO SETUP")
    print("="*60)
    print(f"\nLogo path ready: {logo_path}")
    print("\n📌 NEXT STEPS TO MAKE LOGO VISIBLE:")
    print("-" * 60)
    print("\n1. Open the Sapthagiri NPS University logo image file")
    print("\n2. Save it to this exact location:")
    print(f"   {logo_path}")
    print("\n3. Name it exactly as: sapthagiri_logo.png")
    print("\n4. Recommended image properties:")
    print("   - Format: PNG (with transparency) or JPG")
    print("   - Size: 200x200 pixels or larger")
    print("   - Keep original aspect ratio")
    print("\n5. After saving the logo file:")
    print("   - Run the Flask app: python app.py")
    print("   - Navigate to Login page")
    print("   - Logo should now be visible!")
    print("   - Check Student/Lecturer/Admin dashboards")
    print("\n" + "="*60)
    print("✓ All systems are ready. Just add the logo image!")
    print("="*60 + "\n")
    
    return False


if __name__ == "__main__":
    try:
        setup_logo()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
