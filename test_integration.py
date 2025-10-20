#!/usr/bin/env python3
"""
Test script for the main app integration with AgentCore
"""
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_agentcore_client():
    """Test the AgentCore client"""
    print("🧪 Testing AgentCore Client")
    print("=" * 40)
    
    try:
        from agentcore_client import agentcore_client
        
        # Test health check
        print("1. Testing health check...")
        is_healthy = await agentcore_client.health_check()
        print(f"   ✅ AgentCore healthy: {is_healthy}")
        
        # Test chat
        print("2. Testing chat with AgentCore...")
        response = await agentcore_client.chat_with_agent(
            "I am a data engineer and want to learn AI agents. What should be my learning path?",
            "test_user"
        )
        print(f"   ✅ Chat response received")
        print(f"   Status: {response.get('status')}")
        print(f"   Category: {response.get('category')}")
        print(f"   Message: {response.get('message', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ AgentCore test failed: {e}")
        return False

async def test_api_endpoints():
    """Test the agent API endpoints"""
    print("\n🧪 Testing Agent API Endpoints")
    print("=" * 40)
    
    try:
        import httpx
        
        base_url = "http://localhost:8008"  # Change to your Render URL when deployed
        
        headers = {"Content-Type": "application/json"}
        
        # Test health
        print("1. Testing health endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("   ✅ Health endpoint working")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
        
        # Test skills endpoint
        print("2. Testing skills endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/agent/skills", headers=headers)
            if response.status_code == 200:
                data = response.json()
                skills_count = len(data.get("skills", []))
                print(f"   ✅ Skills endpoint working: {skills_count} skills found")
            else:
                print(f"   ❌ Skills endpoint failed: {response.status_code}")
        
        # Test learning path endpoint
        print("3. Testing learning path endpoint...")
        async with httpx.AsyncClient() as client:
            data = {
                "start_skill": "python",
                "target_skill": "machine learning"
            }
            response = await client.post(
                f"{base_url}/api/agent/learning-path", 
                headers=headers, 
                json=data
            )
            if response.status_code == 200:
                data = response.json()
                path_length = len(data.get("path", []))
                print(f"   ✅ Learning path endpoint working: {path_length} skills in path")
            else:
                print(f"   ❌ Learning path endpoint failed: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API endpoints test failed: {e}")
        return False

async def test_chat_endpoint():
    """Test the chat endpoint"""
    print("\n🧪 Testing Chat Endpoint")
    print("=" * 40)
    
    try:
        import httpx
        
        base_url = "http://localhost:8008"  # Change to your Render URL when deployed
        
        # Test chat endpoint
        print("1. Testing /api/general/chat endpoint...")
        async with httpx.AsyncClient() as client:
            data = {
                "message": "I am a data engineer and want to learn AI agents. What should be my learning path?",
                "user_id": "test_user"
            }
            response = await client.post(
                f"{base_url}/api/general/chat",
                headers={"Content-Type": "application/json"},
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                print("   ✅ Chat endpoint working")
                print(f"   Response: {result.get('ai_response', '')[:100]}...")
                print(f"   Category: {result.get('agent_metadata', {}).get('category')}")
                print(f"   Status: {result.get('agent_metadata', {}).get('status')}")
                
                # Check if it used fallback
                if result.get('agent_metadata', {}).get('fallback'):
                    print("   ⚠️  Used fallback agent (AgentCore may not be configured)")
                else:
                    print("   ✅ Used AgentCore successfully")
                    
            else:
                print(f"   ❌ Chat endpoint failed: {response.status_code}")
                print(f"   Error: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Chat endpoint test failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🚀 Main App Integration Tests")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Check")
    agentcore_url = os.getenv("AGENTCORE_URL")
    agentcore_key = os.getenv("AGENTCORE_API_KEY")
    
    print(f"   AGENTCORE_URL: {'✅ Set' if agentcore_url else '❌ Not set'}")
    print(f"   AGENTCORE_API_KEY: {'✅ Set' if agentcore_key else '❌ Not set'}")
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    # Test 1: AgentCore Client
    if await test_agentcore_client():
        tests_passed += 1
    
    # Test 2: API Endpoints
    if await test_api_endpoints():
        tests_passed += 1
    
    # Test 3: Chat Endpoint
    if await test_chat_endpoint():
        tests_passed += 1
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the configuration and deployment.")
    
    print("\n💡 Next Steps:")
    print("1. Deploy updated code to Render")
    print("2. Set environment variables in Render dashboard")
    print("3. Deploy AgentCore agent")
    print("4. Test end-to-end integration")

if __name__ == "__main__":
    asyncio.run(main())
