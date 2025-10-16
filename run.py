#!/usr/bin/env python3
"""
Convenience script to run the Azure DevOps CLI tool.

This script sets up the proper Python path and imports to run the tool
from the reorganized project structure.

Usage:
    python run.py --help
    python run.py --explain
    python run.py --query-work-items --assigned-to "UserName"
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # Import and run the main entry point
    from entry_points.main import main
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("\nMake sure you have installed the required dependencies:")
    print("pip install -r requirements.txt")
    print("\nAlso ensure your .env file is configured with:")
    print("AZURE_DEVOPS_ORG=<Your Organization>")
    print("AZURE_DEVOPS_PAT=<Your Personal Access Token>")
    sys.exit(1)