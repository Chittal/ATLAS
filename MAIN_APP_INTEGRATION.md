# Main App Integration Guide

This guide shows how the main Render app now integrates with AgentCore instead of using the local agent.

## 🔄 What Changed

### 1. **Agent APIs Moved to Separate Router**
- Moved all agent API endpoints from `app.py` to `routes/agent.py`
- Cleaner separation of concerns
- Easier to maintain and test

### 2. **Updated `/api/general/chat` Endpoint**
- Now calls AgentCore instead of local agent
- Includes fallback to local agent if AgentCore fails
- Maintains same response format for frontend compatibility

### 3. **Added AgentCore Client**
- New `agentcore_client.py` for communicating with deployed agent
- Includes retry logic and error handling
- Supports health checks

## 🔧 Configuration

### Environment Variables

Add these to your Render app environment variables:

```bash
# AgentCore Configuration
AGENTCORE_URL=https://your-agentcore-url.com
AGENTCORE_API_KEY=your_agentcore_api_key
```

## 🚀 How It Works

### Communication Flow

```
User → Frontend → /api/general/chat → AgentCore Client → AgentCore Agent → Render App API → KuzuDB → Response
```

### 1. **User Sends Message**
Frontend sends message to `/api/general/chat`

### 2. **AgentCore Client**
- `agentcore_client.py` sends request to AgentCore
- Includes user message, user ID, and metadata
- Handles authentication and retries

### 3. **AgentCore Agent**
- Receives request and processes with Bedrock Claude
- Calls Render app API endpoints for data
- Returns structured response

### 4. **Response Handling**
- Main app processes AgentCore response
- Maintains same format for frontend compatibility
- Includes fallback to local agent if needed

## 📋 API Endpoints

### AgentCore Communication Endpoints (in `routes/agent.py`)

- `GET /api/agent/skills` - Get all skills
- `GET /api/agent/skill-connections` - Get skill connections
- `POST /api/agent/learning-path` - Find learning paths
- `GET /api/agent/skill-prerequisites` - Get prerequisites
- `GET /api/agent/skill-details` - Get skill details

### Updated Chat Endpoint

- `POST /api/general/chat` - Now calls AgentCore with fallback

## 🔄 Fallback Mechanism

The integration includes a robust fallback mechanism:

1. **Primary**: Try AgentCore agent
2. **Fallback**: Use local agent if AgentCore fails
3. **Error Handling**: Return error message if both fail

```python
try:
    # Try AgentCore first
    result = await agentcore_client.chat_with_agent(user_message, user_id)
except Exception as e:
    # Fallback to local agent
    local_result = request.app.state.agent.execute_graph(user_message)
```

## 🧪 Testing

### 1. **Test AgentCore Connection**

```python
# Test script
from agentcore_client import agentcore_client

async def test_agentcore():
    is_healthy = await agentcore_client.health_check()
    print(f"AgentCore healthy: {is_healthy}")
    
    response = await agentcore_client.chat_with_agent("Hello, test message")
    print(f"Response: {response}")

# Run test
import asyncio
asyncio.run(test_agentcore())
```

### 2. **Test Chat Endpoint**

```bash
curl -X POST "https://your-app.onrender.com/api/general/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "I am a data engineer and want to learn AI agents",
       "user_id": "test_user"
     }'
```

### 3. **Test Agent API Endpoints**

```bash
# Test skills endpoint
curl -X GET "https://your-app.onrender.com/api/agent/skills"

# Test learning path
curl -X POST "https://your-app.onrender.com/api/agent/learning-path" \
     -H "Content-Type: application/json" \
     -d '{
       "start_skill": "python",
       "target_skill": "machine learning"
     }'
```

## 📊 Monitoring

### Health Checks

Monitor these endpoints for system health:

- `GET /health` - Main app health
- AgentCore health check (via client)
- API endpoint availability

### Logging

The integration includes comprehensive logging:

```python
# AgentCore client logs
logger.info("AgentCore request sent", message=message)
logger.error("AgentCore request failed", error=str(e))

# Chat endpoint logs
print(f"API called with message: '{user_message}'")
print("CALLING AGENTCORE AGENT")
print("AgentCore result:", result)
```

## 🔒 Security

### API Authentication

- Agent endpoints protected with `X-API-Key` header
- AgentCore communication uses Bearer token
- Environment variables for sensitive data

### Error Handling

- No sensitive data in error messages
- Graceful fallback mechanisms
- Comprehensive logging for debugging

## 🚀 Deployment Steps

### 1. **Update Environment Variables**

In Render dashboard, add:

```bash
AGENTCORE_URL=https://your-agentcore-url.com
AGENTCORE_API_KEY=your_agentcore_api_key
```

### 2. **Deploy Updated Code**

```bash
git add .
git commit -m "Integrate with AgentCore for chat functionality"
git push
```

### 3. **Test Integration**

1. Test health endpoints
2. Test chat functionality
3. Monitor logs for any issues

## 🔧 Troubleshooting

### Common Issues

1. **AgentCore Connection Failed**
   - Check `AGENTCORE_URL` and `AGENTCORE_API_KEY`
   - Verify AgentCore deployment is healthy
   - Check network connectivity

2. **API Authentication Errors**
   - Verify `AGENTCORE_API_KEY` is correctly set
   - Check AgentCore authentication format

3. **Fallback Not Working**
   - Ensure local agent is still initialized
   - Check database connectivity
   - Verify KuzuDB file exists

### Debug Commands

```bash
# Check app health
curl https://your-app.onrender.com/health

# Test AgentCore client
python -c "
import asyncio
from agentcore_client import agentcore_client
asyncio.run(agentcore_client.health_check())
"

# Test chat endpoint
curl -X POST "https://your-app.onrender.com/api/general/chat" \
     -H "Content-Type: application/json" \
     -d '{"message": "test"}'
```

## 📈 Benefits

### 1. **Scalability**
- AgentCore handles agent scaling
- Main app focuses on data serving
- Better resource utilization

### 2. **Reliability**
- Fallback mechanism ensures uptime
- AgentCore provides enterprise-grade reliability
- Comprehensive error handling

### 3. **Maintainability**
- Clean separation of concerns
- Modular architecture
- Easy to test and debug

## 🎯 Next Steps

1. **Monitor Performance**: Track response times and success rates
2. **Optimize Fallback**: Fine-tune fallback triggers
3. **Add Metrics**: Implement detailed monitoring
4. **Scale AgentCore**: Configure auto-scaling as needed

The integration is now complete! Your main app will use AgentCore for chat functionality while maintaining full compatibility with your existing frontend. 🎉
