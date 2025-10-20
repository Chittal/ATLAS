"""
LLM client for the agent using AWS Bedrock
"""
import json
import asyncio
from typing import Optional, Dict, Any
from config import agent_config
import structlog
import boto3
from botocore.exceptions import ClientError
from langchain_aws import ChatBedrock

logger = structlog.get_logger()

class BedrockClient:
    """AWS Bedrock LLM client"""
    
    def __init__(self, region: str, model_id: str, temperature: float = 0.7, max_tokens: int = 1000):
        self.region = region
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize Bedrock client
        try:
            self.bedrock_client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region
            )
            
            # Initialize LangChain Bedrock client
            self.langchain_client = ChatBedrock(
                model_id=model_id,
                region_name=region,
                model_kwargs={
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            logger.info("Bedrock client initialized", model_id=model_id, region=region)
            
        except Exception as e:
            logger.error("Failed to initialize Bedrock client", error=str(e))
            raise
    
    async def chat_simple(self, prompt: str) -> str:
        """Simple chat completion using Bedrock"""
        try:
            # Use LangChain for async support
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.langchain_client.invoke(prompt)
            )
            
            # Extract content from LangChain response
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error("Bedrock API error", error_code=error_code, error_message=error_message)
            raise Exception(f"Bedrock API error: {error_message}")
        
        except Exception as e:
            logger.error("Bedrock client error", error=str(e))
            raise
    
    async def chat_with_messages(self, messages: list) -> str:
        """Chat completion with message history"""
        try:
            # Convert messages to LangChain format
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            
            langchain_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                elif role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
            
            # Use LangChain for async support
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.langchain_client.invoke(langchain_messages)
            )
            
            # Extract content from LangChain response
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            logger.error("Bedrock messages chat error", error=str(e))
            raise
    
    def get_available_models(self) -> list:
        """Get list of available Bedrock models"""
        try:
            bedrock_client = boto3.client(
                service_name='bedrock',
                region_name=self.region
            )
            
            response = bedrock_client.list_foundation_models()
            models = []
            
            for model in response['modelSummaries']:
                if 'claude' in model['modelId'].lower():
                    models.append({
                        'model_id': model['modelId'],
                        'model_name': model['modelName'],
                        'provider': model['providerName']
                    })
            
            return models
            
        except Exception as e:
            logger.error("Failed to get available models", error=str(e))
            return []

def get_llm_client():
    """Get the Bedrock LLM client based on configuration"""
    try:
        # Validate required configuration
        if not agent_config.aws_region:
            raise ValueError("AWS region not provided")
        
        if not agent_config.bedrock_model_id:
            raise ValueError("Bedrock model ID not provided")
        
        # Create Bedrock client
        client = BedrockClient(
            region=agent_config.aws_region,
            model_id=agent_config.bedrock_model_id,
            temperature=agent_config.temperature,
            max_tokens=agent_config.max_tokens
        )
        
        logger.info("Bedrock client created successfully")
        return client
        
    except Exception as e:
        logger.error("Failed to create Bedrock client", error=str(e))
        raise