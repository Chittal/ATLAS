import asyncio
import logging
import boto3
import json
from config import app_config

client = boto3.client('bedrock-agentcore', region_name='us-east-2')

async def invoke_agent_runtime(user_message: str, session_id: str):
    # boto3 is blocking: run it in a worker thread so the event loop keeps serving other requests
    return await asyncio.to_thread(_invoke_agent_runtime_sync, user_message, session_id)


def _invoke_agent_runtime_sync(user_message: str, session_id: str):
    payload = json.dumps({
        "user_message": user_message
    })
    logging.debug("%s %s", app_config.agent_runtime_arn, "app_config.agent_runtime_arn")
    response = client.invoke_agent_runtime(
        agentRuntimeArn=app_config.agent_runtime_arn,
        runtimeSessionId=session_id,  # Must be 33+ chars
        payload=payload,
        qualifier="DEFAULT" # Optional
    )
    logging.debug("%s %s", response, "response")
    response_body = response['response'].read()
    response_data = json.loads(response_body)
    logging.debug("%s %s", response_data, "response_data")
    return response_data