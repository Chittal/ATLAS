# Personalized Route Planning Agent for AgentCore

This is the AgentCore deployment package for the Personalized Route Planning Agent. This agent provides intelligent learning path recommendations by analyzing skill prerequisites and connections.

## Features

- **Query Classification**: Automatically classifies user queries into route planning, prerequisite, or general queries
- **Skill Extraction**: Extracts relevant skills from natural language queries
- **Learning Path Generation**: Creates personalized learning paths between skills
- **Prerequisite Analysis**: Provides prerequisite information for specific skills
- **General Query Handling**: Handles general learning-related questions

## Architecture

The agent is designed to work with the main Render application:

```
User Query → AgentCore → Personalized Agent → Render App API → KuzuDB → Response
```

## Configuration

### Environment Variables

Copy `env.example` to `.env` and configure the following variables:

#### LLM Configuration
- `LLM_PROVIDER`: LLM provider to use (bedrock)
- `MODEL`: Model name to use
- `AWS_REGION`: AWS region for Bedrock
- `BEDROCK_MODEL_ID`: Bedrock model ID
- `TEMPERATURE`: Model temperature (0.0-1.0)
- `MAX_TOKENS`: Maximum tokens to generate

#### AWS Credentials
- `AWS_ACCESS_KEY_ID`: AWS access key ID
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key

#### Render App Configuration
- `RENDER_APP_URL`: URL of the main Render application

#### AgentCore Configuration
- `AGENTCORE_ENVIRONMENT`: Environment (production, staging, development)
- `AGENT_ID`: Agent ID in AgentCore

#### Logging and Performance
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `API_TIMEOUT`: API timeout in seconds
- `MAX_RETRIES`: Maximum retry attempts for API calls

## Deployment

### Local Testing

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your configuration
```

3. Test the agent:
```bash
python main.py
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t personalized-route-planning-agent .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_REGION=us-east-1 \
  -e RENDER_APP_URL=your_url \
  personalized-route-planning-agent
```

### AgentCore Deployment

1. Package the agent code
2. Deploy to AWS AgentCore
3. Configure environment variables in AgentCore
4. Test the deployment

## API Integration

The agent communicates with the main Render application through the following endpoints:

- `GET /api/agent/skills` - Get all available skills
- `GET /api/agent/skill-connections` - Get skill connections
- `POST /api/agent/learning-path` - Find learning path between skills
- `GET /api/agent/skill-prerequisites` - Get skill prerequisites
- `GET /api/agent/skill-details` - Get skill details
- `GET /health` - Health check

## Query Types

### Route Planning Queries
- "I am a data engineer and want to learn AI agents"
- "How do I get from Python to machine learning?"
- "What's the path from frontend to full stack?"

### Prerequisite Queries
- "What are the prerequisites for Python?"
- "What should I learn before machine learning?"
- "What do I need to know before React?"

### General Queries
- "What is machine learning?"
- "Tell me about web development"
- "How long does it take to learn Python?"

## Error Handling

The agent includes comprehensive error handling:

- API timeout and retry logic
- Graceful degradation when services are unavailable
- Structured logging for debugging
- User-friendly error messages

## Monitoring

The agent uses structured logging with the following information:

- Request/response logging
- Performance metrics
- Error tracking
- API call monitoring

## Security

- API key management through environment variables
- Secure HTTP communication
- Input validation and sanitization
- Rate limiting and timeout protection

## Development

### Project Structure

```
agentcore/
├── main.py                          # Main entry point
├── personalized_route_planning_agent.py  # Core agent logic
├── api_client.py                    # Render app API client
├── llm_client.py                    # LLM client implementations
├── config.py                        # Configuration management
├── schemas.py                       # Data schemas
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Docker configuration
├── env.example                      # Environment variables template
└── README.md                        # This file
```

### Adding New Features

1. Update the agent logic in `personalized_route_planning_agent.py`
2. Add new API endpoints to `api_client.py` if needed
3. Update schemas in `schemas.py`
4. Test locally before deployment

## Troubleshooting

### Common Issues

1. **API Connection Errors**: Check Render app URL and API keys
2. **LLM Errors**: Verify API keys and model names
3. **Timeout Errors**: Increase timeout values or check network connectivity
4. **Memory Issues**: Monitor memory usage and optimize queries

### Logs

Check logs for detailed error information:
```bash
# Local testing
python main.py

# Docker
docker logs container_name

# AgentCore
# Check AgentCore logs in AWS Console
```

## Support

For issues and questions:
1. Check the logs for error details
2. Verify environment configuration
3. Test API connectivity
4. Review the main Render app status
