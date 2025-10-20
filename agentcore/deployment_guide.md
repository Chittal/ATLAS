# AgentCore Deployment Guide

This guide walks you through deploying the Personalized Route Planning Agent to AWS AgentCore and setting up the integration with your main Render application.

## Prerequisites

- AWS Account with AgentCore access
- Main Render application deployed and running
- API keys for LLM providers (Groq, OpenAI, or LiteLLM)
- Docker installed (for local testing)

## Step 1: Prepare the Main Render App

### 1.1 Add Agent API Endpoints

Add the agent API endpoints to your main Render application:

1. Copy the endpoints from `agentcore/render_app_endpoints.py`
2. Add them to your main `app.py`:

```python
# In your main app.py
from agentcore.render_app_endpoints import agent_router
app.include_router(agent_router)
```

### 1.2 Update CORS Settings

Ensure your main app allows requests from AgentCore:

```python
# In your main app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific AgentCore domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 1.3 Add API Authentication (Recommended)

Add API key authentication to protect your agent endpoints:

```python
# Add to your main app.py
from fastapi import HTTPException, Depends, Header

async def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != "your_secret_api_key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Apply to agent routes
@agent_router.get("/skills", dependencies=[Depends(verify_api_key)])
async def get_all_skills():
    # ... existing code
```

### 1.4 Deploy Updated Main App

Deploy your updated main application to Render with the new endpoints.

## Step 2: Prepare Agent for AgentCore

### 2.1 Configure Environment Variables

1. Copy `env.example` to `.env`
2. Configure the following variables:

```bash
# LLM Configuration
LLM_PROVIDER=bedrock
MODEL=claude-3-5-sonnet-20241022
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Render App Configuration
RENDER_APP_URL=https://your-app.onrender.com

# AgentCore Configuration
AGENTCORE_ENVIRONMENT=production
AGENT_ID=your_agent_id
```

### 2.2 Test Locally

Test the agent locally before deployment:

```bash
cd agentcore
pip install -r requirements.txt
python main.py
```

### 2.3 Test API Connectivity

Verify the agent can connect to your Render app:

```python
# Test script
import asyncio
from api_client import render_client

async def test_connection():
    is_healthy = await render_client.health_check()
    print(f"Main app healthy: {is_healthy}")
    
    skills = await render_client.get_all_skills()
    print(f"Found {len(skills)} skills")

asyncio.run(test_connection())
```

## Step 3: Deploy to AgentCore

### 3.1 Package the Agent

Create a deployment package:

```bash
cd agentcore
zip -r agent-package.zip . -x "*.pyc" "__pycache__/*" "*.git*"
```

### 3.2 Deploy to AWS AgentCore

1. **Create Agent in AgentCore Console**:
   - Go to AWS AgentCore console
   - Create new agent
   - Upload the packaged code
   - Configure runtime (Python 3.11)

2. **Set Environment Variables**:
   - Add all environment variables from your `.env` file
   - Ensure API keys are properly configured

3. **Configure Agent Settings**:
   - Set memory and timeout limits
   - Configure logging level
   - Set up monitoring

### 3.3 Test AgentCore Deployment

Test the deployed agent:

```bash
# Test payload
{
  "message": "I am a data engineer and want to learn AI agents. What should be my learning path?",
  "user_id": "test_user",
  "session_id": "test_session"
}
```

## Step 4: Integrate with Main App

### 4.1 Add AgentCore Integration

Add AgentCore integration to your main app:

```python
# In your main app.py
import httpx
import asyncio

class AgentCoreClient:
    def __init__(self, agentcore_url: str, api_key: str):
        self.url = agentcore_url
        self.api_key = api_key
    
    async def call_agent(self, message: str, user_id: str = None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/invoke",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "message": message,
                    "user_id": user_id,
                    "session_id": f"session_{user_id}"
                }
            )
            return response.json()

# Add chat endpoint
@app.post("/api/chat")
async def chat_with_agent(
    message: str = Body(...),
    user_id: str = Body(None)
):
    agentcore_client = AgentCoreClient(
        agentcore_url=os.getenv("AGENTCORE_URL"),
        api_key=os.getenv("AGENTCORE_API_KEY")
    )
    
    response = await agentcore_client.call_agent(message, user_id)
    return response
```

### 4.2 Update Frontend

Update your frontend to use the new chat endpoint:

```javascript
// Example frontend integration
async function sendMessage(message) {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            user_id: getCurrentUserId()
        })
    });
    
    const data = await response.json();
    return data;
}
```

## Step 5: Monitoring and Maintenance

### 5.1 Set Up Monitoring

1. **AgentCore Monitoring**:
   - Monitor agent execution metrics
   - Set up alerts for failures
   - Track response times

2. **Main App Monitoring**:
   - Monitor API endpoint performance
   - Track database query performance
   - Set up health checks

### 5.2 Logging

Configure structured logging:

```python
# In your main app
import logging
import structlog

logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# Log agent interactions
logger.info("Agent request", message=message, user_id=user_id)
logger.info("Agent response", response=response)
```

### 5.3 Error Handling

Implement comprehensive error handling:

```python
# In your main app
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## Step 6: Testing End-to-End

### 6.1 Test Scenarios

Test the complete flow:

1. **Route Planning**:
   - "I am a data engineer and want to learn AI agents"
   - "How do I get from Python to machine learning?"

2. **Prerequisites**:
   - "What are the prerequisites for Python?"
   - "What should I learn before machine learning?"

3. **General Queries**:
   - "What is machine learning?"
   - "Tell me about web development"

### 6.2 Performance Testing

Test performance under load:

```bash
# Load testing
ab -n 100 -c 10 -H "Content-Type: application/json" \
   -p test_payload.json \
   https://your-app.onrender.com/api/chat
```

## Troubleshooting

### Common Issues

1. **AgentCore Connection Errors**:
   - Check environment variables
   - Verify API keys
   - Test network connectivity

2. **Main App API Errors**:
   - Check CORS settings
   - Verify endpoint URLs
   - Test API authentication

3. **Database Connection Issues**:
   - Check KuzuDB initialization
   - Verify database file permissions
   - Test database queries

### Debug Commands

```bash
# Test agent locally
cd agentcore
python main.py

# Test API connectivity
curl -X GET "https://your-app.onrender.com/api/agent/skills" \
     -H "Authorization: Bearer your_api_key"

# Check agent health
curl -X GET "https://your-app.onrender.com/health"
```

## Security Considerations

1. **API Key Management**:
   - Use environment variables
   - Rotate keys regularly
   - Monitor key usage

2. **Rate Limiting**:
   - Implement rate limiting on endpoints
   - Set up abuse detection
   - Monitor for unusual patterns

3. **Input Validation**:
   - Validate all inputs
   - Sanitize user messages
   - Implement query length limits

## Next Steps

1. **Optimization**:
   - Cache frequent queries
   - Optimize database queries
   - Implement response compression

2. **Features**:
   - Add user preference learning
   - Implement conversation history
   - Add progress tracking

3. **Scaling**:
   - Implement load balancing
   - Add database replication
   - Set up auto-scaling
