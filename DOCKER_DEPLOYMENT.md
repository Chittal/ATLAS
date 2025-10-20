# Docker Deployment Guide for Learning Map Application

This guide explains how to deploy the Learning Map application using Docker on Render.

## Files Created for Docker Deployment

1. **Dockerfile** - Defines the container environment
2. **.dockerignore** - Excludes unnecessary files from Docker build
3. **render.yaml** - Render-specific deployment configuration
4. **Health check endpoint** - Added to app.py for container health monitoring

## Prerequisites

- Docker installed locally (for testing)
- Render account
- Environment variables configured

## Environment Variables Required

Set these environment variables in your Render dashboard:

### Required Variables:
- `POCKETBASE_URL` - URL of your PocketBase instance
- `POCKETBASE_EMAIL` - PocketBase admin email
- `POCKETBASE_PASSWORD` - PocketBase admin password
- `SECRET` - Application secret key

### Optional Variables:
- `API_BASE` - API base URL
- `API_KEY` - API key for external services
- `MODEL` - Default model (default: llama3.1:8b)
- `CUSTOM_LLM_PROVIDER` - Custom LLM provider
- `GROQ_API_KEY` - Groq API key
- `OPENAI_API_KEY` - OpenAI API key

## Local Docker Testing

1. Build the Docker image:
```bash
docker build -t learning-map-app .
```

2. Run the container locally:
```bash
docker run -p 8008:8008 \
  -e POCKETBASE_URL=your_pocketbase_url \
  -e POCKETBASE_EMAIL=your_email \
  -e POCKETBASE_PASSWORD=your_password \
  -e SECRET=your_secret_key \
  learning-map-app
```

3. Test the application:
```bash
curl http://localhost:8008/health
```

## Deploying to Render

### Method 1: Using Render Dashboard

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Configure the service:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11
4. Set all required environment variables
5. Deploy

### Method 2: Using render.yaml

1. Ensure `render.yaml` is in your repository root
2. Push to your connected repository
3. Render will automatically detect and use the configuration

## Database Considerations

The application uses:
- **Kuzu Database** (`skills_graph.db`) - Graph database for learning paths
- **PocketBase** - External database service
- **SQLite files** - Local data storage

### For Production:
- Consider using external database services for persistent storage
- The current setup includes database files in the container, which may not persist across deployments
- For production, you might want to:
  - Use external PocketBase instance
  - Implement database initialization scripts
  - Use volume mounts for persistent data

## Health Monitoring

The application includes a health check endpoint at `/health` that returns:
```json
{
  "status": "healthy",
  "message": "Learning Map API is running"
}
```

## Troubleshooting

### Common Issues:

1. **Port Configuration**: Ensure the application uses `$PORT` environment variable for Render
2. **Environment Variables**: Verify all required environment variables are set
3. **Database Connections**: Check PocketBase connectivity
4. **Memory Usage**: The application uses AI/ML libraries which may require more memory

### Logs:
Check Render logs for detailed error information:
```bash
render logs --service learning-map-app
```

## Performance Considerations

- The application includes heavy ML/AI dependencies
- Consider using Render's Standard or Pro plans for better performance
- Monitor memory usage and CPU utilization
- Consider implementing caching for frequently accessed data

## Security Notes

- Never commit `.env` files to version control
- Use Render's secure environment variable storage
- Ensure PocketBase credentials are properly secured
- Consider implementing rate limiting for production use
