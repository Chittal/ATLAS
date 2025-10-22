import boto3
import json
from config import app_config

client = boto3.client('bedrock-agentcore', region_name='us-east-2')

async def invoke_agent_runtime(user_message: str, session_id: str):
    payload = json.dumps({
        "user_message": user_message
    })
    print(app_config.agent_runtime_arn, "app_config.agent_runtime_arn")
    response = client.invoke_agent_runtime(
        agentRuntimeArn=app_config.agent_runtime_arn,
        runtimeSessionId=session_id,  # Must be 33+ chars
        payload=payload,
        qualifier="DEFAULT" # Optional
    )
    print(response, "response")
    response_body = response['response'].read()
    response_data = json.loads(response_body)
    print(response_data, "response_data")
    return response_data