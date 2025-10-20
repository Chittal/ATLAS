# API Communication Setup Guide

This guide walks you through setting up API communication between your AgentCore agent and the main Render application.

## ✅ What We've Added

### 1. **Agent API Endpoints** (Added to `app.py`)
- `GET /api/agent/skills` - Get all available skills
- `GET /api/agent/skill-connections` - Get skill connections
- `POST /api/agent/learning-path` - Find learning path between skills
- `GET /api/agent/skill-prerequisites` - Get skill prerequisites
- `GET /api/agent/skill-details` - Get skill details

### 2. **API Authentication**
- Optional API key authentication via `X-API-Key` header
- Configurable via `RENDER_API_KEY` environment variable

### 3. **CORS Configuration**
- Updated to allow AgentCore communication
- Supports all necessary HTTP methods

## 🔧 Configuration Steps

### Step 1: Set Up Environment Variables

Add to your main app's environment variables:

```bash
# API Authentication (for AgentCore communication)
RENDER_API_KEY=your_secret_api_key_here
```

### Step 2: Test Locally (Optional)

1. **Start your main app**:
```bash
python app.py
```

2. **Test the endpoints**:
```bash
python test_api_endpoints.py
```

### Step 3: Deploy to Render

1. **Commit your changes**:
```bash
git add app.py
git commit -m "Add agent API endpoints for AgentCore communication"
git push
```

2. **Deploy to Render**:
- Render will automatically deploy your updated app
- The new API endpoints will be available at `https://your-app.onrender.com/api/agent/`

## 🔗 API Endpoint Details

### GET /api/agent/skills
**Purpose**: Get all available skills from the database

**Request**:
```bash
curl -X GET "https://your-app.onrender.com/api/agent/skills" \
     -H "X-API-Key: your_api_key"
```

**Response**:
```json
{
  "skills": [
    {
      "id": "skill_id",
      "name": "Python",
      "description": "Learn Python skills and concepts",
      "order_index": 1
    }
  ],
  "status": "success"
}
```

### POST /api/agent/learning-path
**Purpose**: Find learning path between two skills

**Request**:
```bash
curl -X POST "https://your-app.onrender.com/api/agent/learning-path" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key" \
     -d '{
       "start_skill": "python",
       "target_skill": "machine learning"
     }'
```

**Response**:
```json
{
  "path": [
    {
      "id": "skill_id_1",
      "name": "Python",
      "description": "Learn Python skills and concepts",
      "order_index": 1
    },
    {
      "id": "skill_id_2", 
      "name": "Machine Learning",
      "description": "Learn Machine Learning skills and concepts",
      "order_index": 10
    }
  ],
  "status": "success"
}
```

### GET /api/agent/skill-prerequisites
**Purpose**: Get prerequisites for a specific skill

**Request**:
```bash
curl -X GET "https://your-app.onrender.com/api/agent/skill-prerequisites?skill_name=python" \
     -H "X-API-Key: your_api_key"
```

**Response**:
```json
{
  "prerequisites": [
    {
      "id": "prereq_id",
      "name": "Computer Science"
    }
  ],
  "status": "success"
}
```

## 🔒 Security Considerations

### API Key Authentication
- Set `RENDER_API_KEY` environment variable in Render
- AgentCore will use this key to authenticate requests
- If no API key is set, endpoints are publicly accessible

### Rate Limiting (Recommended)
Consider adding rate limiting for production:

```python
# Add to app.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add to endpoints
@limiter.limit("10/minute")
@app.get("/api/agent/skills")
async def get_all_skills():
    # ... existing code
```

## 🧪 Testing

### Local Testing
```bash
# Start your app
python app.py

# Test endpoints
python test_api_endpoints.py
```

### Production Testing
```bash
# Test with curl
curl -X GET "https://your-app.onrender.com/health"
curl -X GET "https://your-app.onrender.com/api/agent/skills" \
     -H "X-API-Key: your_api_key"
```

## 🚀 AgentCore Configuration

### Update AgentCore Environment Variables
Set these in your AgentCore deployment:

```bash
# Render App Configuration
RENDER_APP_URL=https://your-app.onrender.com
RENDER_API_KEY=your_secret_api_key_here
```

### Test AgentCore Connection
The agent will automatically test the connection when it starts:

```python
# In agentcore/api_client.py
async def health_check(self) -> bool:
    """Check if the main app is healthy"""
    try:
        response = await self._make_request("GET", "/health")
        return response.get("status") == "healthy"
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return False
```

## 📊 Monitoring

### Health Checks
- Monitor `/health` endpoint for app status
- Set up alerts for API endpoint failures
- Track response times and error rates

### Logging
The API endpoints include comprehensive logging:

```python
# Example logging in endpoints
logger.info("API request received", endpoint="/api/agent/skills")
logger.error("Database error", error=str(e))
```

## 🔧 Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if `RENDER_API_KEY` is set correctly
   - Verify the API key matches between Render and AgentCore

2. **500 Internal Server Error**
   - Check if KuzuDB is properly initialized
   - Verify database file exists and is accessible

3. **CORS Errors**
   - Ensure CORS middleware is configured correctly
   - Check if AgentCore is sending proper headers

### Debug Commands

```bash
# Check app health
curl https://your-app.onrender.com/health

# Test API endpoint
curl -H "X-API-Key: your_key" \
     https://your-app.onrender.com/api/agent/skills

# Check logs in Render dashboard
```

## 📈 Next Steps

1. **Deploy Updated App**: Push changes to Render
2. **Configure AgentCore**: Set environment variables
3. **Test Integration**: Verify agent can communicate with app
4. **Monitor Performance**: Set up logging and monitoring
5. **Scale as Needed**: Adjust based on usage patterns

The API communication setup is now complete! Your AgentCore agent will be able to communicate with your Render app to access KuzuDB data. 🎉
