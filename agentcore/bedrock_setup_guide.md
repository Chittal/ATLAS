# AWS Bedrock Setup Guide for AgentCore

This guide walks you through setting up AWS Bedrock with Claude models for your AgentCore deployment.

## Prerequisites

- AWS Account with access to Bedrock
- AWS CLI configured (optional but recommended)
- Appropriate AWS permissions for Bedrock

## Step 1: Enable Bedrock Models

### 1.1 Access Bedrock Console

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Sign in to your AWS account
3. Select your preferred region (e.g., `us-east-1`)

### 1.2 Enable Claude Models

1. In the Bedrock console, go to **Model access**
2. Click **Request model access**
3. Select **Claude 3.5 Sonnet** (recommended)
4. Click **Request model access**
5. Wait for approval (usually instant for Claude models)

### 1.3 Verify Model Access

1. Go to **Playground** in the Bedrock console
2. Select **Claude 3.5 Sonnet**
3. Try a simple prompt to verify access

## Step 2: Configure AWS Credentials

### 2.1 Using IAM User (Recommended for AgentCore)

1. **Create IAM User**:
   - Go to [IAM Console](https://console.aws.amazon.com/iam/)
   - Create new user: `agentcore-bedrock-user`
   - Attach policy: `AmazonBedrockFullAccess` (or create custom policy)

2. **Create Access Keys**:
   - Go to **Security credentials** tab
   - Click **Create access key**
   - Choose **Application running outside AWS**
   - Save the Access Key ID and Secret Access Key

### 2.2 Using IAM Role (Recommended for EC2/ECS)

If deploying on AWS infrastructure:

1. Create IAM role with Bedrock permissions
2. Attach role to EC2 instance or ECS task
3. No need for explicit credentials in environment variables

### 2.3 Custom IAM Policy

For production, create a minimal policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
        }
    ]
}
```

## Step 3: Configure Environment Variables

### 3.1 Required Variables

Set these in your AgentCore environment:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key

# Bedrock Configuration
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
MODEL=claude-3-5-sonnet-20241022

# Model Parameters
TEMPERATURE=0.7
MAX_TOKENS=1000
```

### 3.2 Available Claude Models

Here are the available Claude models in Bedrock:

| Model ID | Description | Max Tokens | Recommended Use |
|----------|-------------|------------|-----------------|
| `anthropic.claude-3-5-sonnet-20241022-v2:0` | Latest Claude 3.5 Sonnet | 8,192 | General purpose, best performance |
| `anthropic.claude-3-5-haiku-20241022-v1:0` | Claude 3.5 Haiku | 8,192 | Fast responses, lower cost |
| `anthropic.claude-3-opus-20240229-v1:0` | Claude 3 Opus | 4,096 | Complex reasoning |
| `anthropic.claude-3-sonnet-20240229-v1:0` | Claude 3 Sonnet | 4,096 | Balanced performance |

## Step 4: Test Bedrock Connection

### 4.1 Local Testing

Run the test script:

```bash
cd agentcore
python test_bedrock.py
```

Expected output:
```
🔍 Testing Bedrock connection...
✅ Environment variables configured
🤖 Creating Bedrock client...
✅ Bedrock client created successfully
💬 Testing simple chat...
✅ Chat response: Bedrock connection successful!
📋 Checking available models...
✅ Found X Claude models available
🎉 All tests passed! Bedrock is ready to use.
```

### 4.2 Test Agent Functionality

```bash
python main.py
```

Expected output:
```
🚀 Testing Personalized Route Planning Agent with Bedrock Claude
============================================================
✅ Test response received:
{
  "message": "Based on your background as a data engineer...",
  "status": "success",
  "category": "ROUTE_PLANNING",
  "path_objects": [...],
  "error": null,
  "metadata": {...}
}
```

## Step 5: Deploy to AgentCore

### 5.1 Package Agent

```bash
cd agentcore
zip -r agent-package.zip . -x "*.pyc" "__pycache__/*" "*.git*" "test_*.py"
```

### 5.2 Configure AgentCore Environment

In AgentCore console, set environment variables:

- `AWS_REGION`: `us-east-1`
- `AWS_ACCESS_KEY_ID`: Your access key
- `AWS_SECRET_ACCESS_KEY`: Your secret key
- `BEDROCK_MODEL_ID`: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `RENDER_APP_URL`: Your Render app URL

### 5.3 Deploy and Test

1. Upload the agent package
2. Configure runtime (Python 3.11)
3. Set memory (512MB minimum)
4. Deploy and test

## Step 6: Monitoring and Troubleshooting

### 6.1 CloudWatch Logs

Monitor Bedrock usage in CloudWatch:

1. Go to CloudWatch console
2. Check **Logs** → **Log groups**
3. Look for Bedrock-related logs

### 6.2 Common Issues

#### Issue: "Model access denied"
**Solution**: Enable model access in Bedrock console

#### Issue: "Invalid credentials"
**Solution**: Check AWS credentials and permissions

#### Issue: "Region not supported"
**Solution**: Use supported regions: `us-east-1`, `us-west-2`, `eu-west-1`

#### Issue: "Model not found"
**Solution**: Verify model ID and region match

### 6.3 Cost Monitoring

Monitor Bedrock costs:

1. Go to [AWS Cost Explorer](https://console.aws.amazon.com/cost-management/home#/cost-explorer)
2. Filter by **Bedrock** service
3. Set up billing alerts

## Step 7: Production Considerations

### 7.1 Security

- Use IAM roles instead of access keys when possible
- Implement least-privilege permissions
- Rotate credentials regularly
- Use AWS Secrets Manager for sensitive data

### 7.2 Performance

- Adjust `MAX_TOKENS` based on use case
- Use appropriate `TEMPERATURE` for consistency
- Implement caching for repeated queries
- Monitor response times

### 7.3 Scaling

- Set up auto-scaling policies
- Implement rate limiting
- Use connection pooling
- Monitor resource usage

## Step 8: Advanced Configuration

### 8.1 Custom Model Parameters

```python
# In config.py, you can customize:
class AgentConfig(BaseSettings):
    temperature: float = Field(default=0.7)  # 0.0-1.0
    max_tokens: int = Field(default=1000)    # 1-8192
    top_p: float = Field(default=1.0)        # 0.0-1.0
    top_k: int = Field(default=250)          # 1-500
```

### 8.2 Error Handling

The agent includes comprehensive error handling:

- Automatic retries for transient errors
- Fallback responses for service unavailability
- Detailed logging for debugging
- Graceful degradation

### 8.3 Custom Prompts

You can customize prompts in the agent:

```python
# In personalized_route_planning_agent.py
# Modify the prompt templates for different behavior
```

## Support and Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude API Documentation](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [LangChain AWS Integration](https://python.langchain.com/docs/integrations/providers/aws_bedrock)
- [AWS Support](https://console.aws.amazon.com/support/)

## Cost Optimization Tips

1. **Use appropriate models**: Haiku for simple tasks, Sonnet for complex reasoning
2. **Optimize prompts**: Shorter, more focused prompts reduce token usage
3. **Implement caching**: Cache responses for repeated queries
4. **Monitor usage**: Set up billing alerts and monitor token consumption
5. **Batch requests**: When possible, batch multiple requests together
