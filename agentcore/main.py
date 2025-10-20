"""
Main entry point for the AgentCore deployment
"""
import asyncio
import json
from typing import Dict, Any
from schemas import AgentRequest, AgentResponse
from personalized_route_planning_agent import agent
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

async def handle_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming requests from AgentCore
    
    Expected event format:
    {
        "message": "User message",
        "user_id": "optional_user_id",
        "session_id": "optional_session_id",
        "metadata": {}
    }
    """
    try:
        logger.info("Processing request", event=event)
        
        # Extract message from event
        message = event.get("message", "")
        if not message:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Message is required",
                    "status": "error"
                })
            }
        
        # Create agent request
        agent_request = AgentRequest(
            message=message,
            user_id=event.get("user_id"),
            session_id=event.get("session_id"),
            metadata=event.get("metadata", {})
        )
        
        # Execute agent
        response = await agent.execute(agent_request)
        
        # Return response
        return {
            "statusCode": 200,
            "body": json.dumps(response)
        }
        
    except Exception as e:
        logger.error("Request handling error", error=str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "status": "error"
            })
        }

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for AgentCore deployment
    """
    try:
        # Run the async handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(handle_request(event))
        loop.close()
        return result
    except Exception as e:
        logger.error("Lambda handler error", error=str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "status": "error"
            })
        }

async def main():
    """
    Main function for testing the agent locally
    """
    print("🚀 Testing Personalized Route Planning Agent with Bedrock Claude")
    print("=" * 60)
    
    # Test the agent
    test_request = AgentRequest(
        message="I am a data engineer and I want to learn AI agents. What should be my learning path?",
        user_id="test_user",
        session_id="test_session",
        metadata={"test": True}
    )
    
    try:
        response = await agent.execute(test_request)
        print("✅ Test response received:")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error("Agent test failed", error=str(e))

if __name__ == "__main__":
    asyncio.run(main())
