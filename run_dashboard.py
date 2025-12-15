"""
Simple script to run the Social Media Analytics Dashboard
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'streamlit', 'plotly', 'pandas', 'networkx', 'pyvis'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    return True

def check_data_file():
    """Check if the data file exists."""
    data_file = "data/data.jsonl"
    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        print("Please ensure the data file exists before running the dashboard.")
        return False
    return True

def run_dashboard():
    """Run the Streamlit dashboard."""
    if not check_dependencies():
        return
    
    if not check_data_file():
        return
    
    print("Starting Social Media Analytics Dashboard...")
    print("Dashboard will open in your default browser at http://localhost:8501")
    print("Press Ctrl+C to stop the dashboard")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nDashboard stopped.")

if __name__ == "__main__":
    run_dashboard()