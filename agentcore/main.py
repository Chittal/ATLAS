from bedrock_agentcore.runtime import BedrockAgentCoreApp
from personalized_route_planning_agent import agent, graph
from config import app_config

app = BedrockAgentCoreApp()

@app.entrypoint
async def agent_invocation(payload):
    """Handler for agent invocation"""
    user_message = payload.get("user_message")
    if user_message is None:
        raise ValueError("User message is required")
    result = agent.invoke(user_message, graph)
    print("result", result)
    return {
        "status": "success",
        "status_code": 200,
        "message": "Agent invocation successful",
        "agent_result": result
    }

if __name__ == "__main__":
    app.run()