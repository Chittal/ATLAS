#!/usr/bin/env python3
"""
Test script for the agent API endpoints
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = "http://localhost:8008"  # Change to your Render app URL when deployed
API_KEY = os.getenv("RENDER_API_KEY")  # Set this in your .env file

def test_endpoint(endpoint, method="GET", data=None, params=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"✅ {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
        else:
            print(f"   Error: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ {method} {endpoint}")
        print(f"   Error: {e}")
        return False

def main():
    """Test all agent API endpoints"""
    print("🧪 Testing Agent API Endpoints")
    print("=" * 50)
    
    # Test health check first
    print("\n1. Testing Health Check")
    test_endpoint("/health")
    
    # Test agent endpoints
    print("\n2. Testing Agent Endpoints")
    
    # Test get all skills
    print("\n   Testing GET /api/agent/skills")
    test_endpoint("/api/agent/skills")
    
    # Test get skill connections
    print("\n   Testing GET /api/agent/skill-connections")
    test_endpoint("/api/agent/skill-connections")
    
    # Test learning path
    print("\n   Testing POST /api/agent/learning-path")
    test_endpoint("/api/agent/learning-path", method="POST", data={
        "start_skill": "python",
        "target_skill": "machine learning"
    })
    
    # Test skill prerequisites
    print("\n   Testing GET /api/agent/skill-prerequisites")
    test_endpoint("/api/agent/skill-prerequisites", params={"skill_name": "python"})
    
    # Test skill details
    print("\n   Testing GET /api/agent/skill-details")
    test_endpoint("/api/agent/skill-details", params={"skill_name": "python"})
    
    print("\n🎉 API endpoint testing completed!")

if __name__ == "__main__":
    main()
