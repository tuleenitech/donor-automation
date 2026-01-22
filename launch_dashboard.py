#!/usr/bin/env python3
"""
Quick launcher for the Donor Opportunity Dashboard
Run this to start the dashboard
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required = ['streamlit', 'pandas', 'plotly']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Missing required packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n💡 Install them with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║              🎯 DONOR OPPORTUNITY DASHBOARD LAUNCHER                 ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
 
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    print("✅ All dependencies installed\n")
    

    if not os.path.exists('dashboard.py'):
        print("⚠️  dashboard.py not found in current directory")
        print("💡 Make sure you've saved the dashboard code as 'dashboard.py'")
        sys.exit(1)
    
    print("🚀 Launching dashboard...")
    print("\n" + "="*70)
    print("The dashboard will open in your browser automatically")
    print("If it doesn't, navigate to: http://localhost:8501")
    print("\nPress Ctrl+C to stop the dashboard")
    print("="*70 + "\n")
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable,
            '-m',
            'streamlit',
            'run',
            'dashboard.py',
            '--server.headless=false'
        ])
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped. Goodbye!")
    except Exception as e:
        print(f"\n⚠️  Error launching dashboard: {e}")
        print("\n💡 Try running manually:")
        print("   streamlit run dashboard.py")

if __name__ == "__main__":
    main()