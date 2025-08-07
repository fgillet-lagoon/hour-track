#!/usr/bin/env python3
"""
Health check script for the Lagoon Time Tracker application.
This script verifies that the application is running correctly.
"""

import sys
import requests
import time

def check_health():
    """Check if the application is healthy."""
    try:
        # Try to connect to the main application
        response = requests.get('http://localhost:5000/', timeout=10)
        
        if response.status_code == 200:
            print("✓ Application is healthy")
            return True
        else:
            print(f"✗ Application returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to application")
        return False
    except requests.exceptions.Timeout:
        print("✗ Application request timed out")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def main():
    """Main health check function."""
    print("Checking Lagoon Time Tracker health...")
    
    # Wait a bit for the application to start
    time.sleep(2)
    
    if check_health():
        print("Health check passed!")
        sys.exit(0)
    else:
        print("Health check failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()