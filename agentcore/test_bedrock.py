"""
Test script to verify Bedrock connectivity and configuration
"""
import asyncio
import os
from dotenv import load_dotenv
from llm_client import get_llm_client
import structlog

# Load environment variables
load_dotenv()

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def test_bedrock_connection():
    """Test Bedrock connection and basic functionality"""
    try:
        print("🔍 Testing Bedrock connection...")
        
        # Test configuration
        required_vars = [
            'AWS_REGION',
            'BEDROCK_MODEL_ID',
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        print("✅ Environment variables configured")
        
        # Test LLM client creation
        print("🤖 Creating Bedrock client...")
        llm_client = get_llm_client()
        print("✅ Bedrock client created successfully")
        
        # Test simple chat
        print("💬 Testing simple chat...")
        test_prompt = "Hello! Please respond with 'Bedrock connection successful!' if you can read this message."
        
        response = await llm_client.chat_simple(test_prompt)
        print(f"✅ Chat response: {response}")
        
        # Test available models (optional)
        print("📋 Checking available models...")
        try:
            models = llm_client.get_available_models()
            print(f"✅ Found {len(models)} Claude models available")
            for model in models[:3]:  # Show first 3 models
                print(f"   - {model['model_name']} ({model['model_id']})")
        except Exception as e:
            print(f"⚠️  Could not list models: {e}")
        
        print("\n🎉 All tests passed! Bedrock is ready to use.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error("Bedrock test failed", error=str(e))
        return False

async def test_agent_functionality():
    """Test the agent with a sample query"""
    try:
        print("\n🧪 Testing agent functionality...")
        
        from personalized_route_planning_agent import agent
        from schemas import AgentRequest
        
        # Test query
        test_request = AgentRequest(
            message="I am a data engineer and want to learn AI agents. What should be my learning path?",
            user_id="test_user",
            session_id="test_session",
            metadata={"test": True}
        )
        
        print("📝 Sending test query...")
        response = await agent.execute(test_request)
        
        print(f"✅ Agent response received:")
        print(f"   Status: {response['status']}")
        print(f"   Category: {response['category']}")
        print(f"   Message: {response['message'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        logger.error("Agent test failed", error=str(e))
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Bedrock Agent Tests\n")
    
    # Test 1: Bedrock connection
    bedrock_ok = await test_bedrock_connection()
    
    if not bedrock_ok:
        print("\n❌ Bedrock connection failed. Please check your configuration.")
        return
    
    # Test 2: Agent functionality (optional, requires Render app)
    print("\n" + "="*50)
    test_agent = input("Test agent functionality? (requires Render app connection) [y/N]: ").lower() == 'y'
    
    if test_agent:
        agent_ok = await test_agent_functionality()
        if agent_ok:
            print("\n🎉 All tests completed successfully!")
        else:
            print("\n⚠️  Agent test failed, but Bedrock connection is working.")
    else:
        print("\n✅ Bedrock connection test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
