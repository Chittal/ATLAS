from langchain_aws import ChatBedrock
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from typing import Optional
from config import app_config


class BedrockClient:
    """AWS Bedrock client class for handling LLM interactions"""
    
    def __init__(self, model: str = None):
        # Use provided model or fallback to config or default
        self.model = app_config.model
        
        if not self.model:
            raise ValueError("Model name is required but not provided")
            
        # Get AWS credentials from environment variables
        self.aws_access_key_id = app_config.aws_access_key_id
        self.aws_secret_access_key = app_config.aws_secret_access_key
        self.aws_region = app_config.aws_region
        
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) are required")
            
        try:
            # Initialize ChatBedrock LLM
            print("I AM AT BEDROCK CLIENT=============")
            print("Model", self.model)
            print("AWS Access Key ID", self.aws_access_key_id)
            print("AWS Secret Access Key", self.aws_secret_access_key)
            print("AWS Region", self.aws_region)
            self.llm = ChatBedrock(
                model_id=self.model,
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                model_kwargs={
                    "temperature": 0.5,
                    "max_tokens": 300,
                    "top_p": 0.95
                }
            )
        except Exception as e:
            print("I AM AT BEDROCK CLIENT EXCEPTION=============")
            print(f"Warning: Could not initialize Bedrock with model '{self.model}': {e}")
    
    def chat(self, messages: list[dict], system_prompt: Optional[str] = None) -> str:
        """
        Main chat function using AWS Bedrock
        
        Args:
            messages: List of message dictionaries with 'user' and/or 'ai' keys
            system_prompt: Optional system prompt to set context
            
        Returns:
            LLM response content
        """
        chat_messages = []
        
        # Add system message if provided
        if system_prompt:
            chat_messages.append(SystemMessage(content=system_prompt))
        
        # Process messages
        for msg in messages:
            if "ai" in msg and msg["ai"]:
                chat_messages.append(AIMessage(content=msg["ai"]))
            if "user" in msg and msg["user"]:
                chat_messages.append(HumanMessage(content=msg["user"]))
        
        # Send the message to the model
        response = self.llm.invoke(chat_messages)
        return response.content
    
    def chat_simple(self, prompt: str) -> str:
        """
        Simple chat function for single prompt
        
        Args:
            prompt: The user prompt/message
            
        Returns:
            LLM response content
        """
        try:
            # Create a simple message list
            messages = [HumanMessage(content=prompt)]
            
            # Send the message to the model
            response = self.llm.invoke(messages)
            print("RESPONSE===========", response)
            return response.content
        except Exception as e:
            print(f"Error in Bedrock chat_simple: {e}")
            return f"I encountered an error: {str(e)}"

    def bind_tools(self, tools: list[dict]):
        """
        Bind tools to the LLM
        """
        self.llm = self.llm.bind_tools(tools)
        return self.llm


# Legacy function for backward compatibility
def call_bedrock_model(
    messages: list[dict], 
    system_prompt: Optional[str], 
    model: str,
    temperature: float = 0.5,
    max_tokens: int = 300,
    top_p: float = 0.95,
    stop: list = None):
    """
    Legacy function - use BedrockClient class instead
    """
    client = BedrockClient(model=model)
    client.llm.model_kwargs["temperature"] = temperature
    client.llm.model_kwargs["max_tokens"] = max_tokens
    client.llm.model_kwargs["top_p"] = top_p
    if stop:
        client.llm.model_kwargs["stop"] = stop
    
    return client.chat(messages, system_prompt)
