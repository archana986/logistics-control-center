#!/usr/bin/env python3
"""
Test script for the Databricks model backend API
"""

import requests
import json
import sys

BACKEND_URL = "http://localhost:8001"

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print(f"✅ Health check: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_generate_message():
    """Test the message generation endpoint"""
    print("\nTesting message generation...")
    
    payload = {
        "customerName": "Acme Corporation",
        "laneId": "LAX-JFK-001",
        "strategy": {
            "strategy": "air freight",
            "deltaETAminutes": -30
        },
        "incidentSummary": "Highway closure due to severe weather",
        "incident": {
            "type": "weather_delay",
            "ref": "INC-2024-001",
            "cause": "Severe thunderstorms on I-40",
            "impactMinutes": 120,
            "confidence": 0.95
        }
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/generate-customer-update",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Generate message: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nSource: {data['source']}")
            print(f"\nGenerated Message:\n{'-' * 80}")
            print(data['message'])
            print('-' * 80)
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generate message failed: {e}")
        return False

def main():
    print("=" * 80)
    print("Databricks Model Backend API Test")
    print("=" * 80)
    print()
    
    # Test health endpoint
    if not test_health():
        print("\n❌ Backend is not running or not responding")
        print("Please start the backend with: python -m uvicorn backend.main:app --reload")
        sys.exit(1)
    
    # Test message generation
    if not test_generate_message():
        print("\n⚠️  Message generation test failed")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print("=" * 80)

if __name__ == "__main__":
    main()


