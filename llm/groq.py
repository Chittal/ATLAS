from langchain_groq import ChatGroq
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from typing import Optional
import os
from config import app_config


class GroqClient:
    """Groq client class for handling LLM interactions"""
    
    def __init__(self, model: str = None):
        # Use provided model or fallback to config or default
        self.model = "llama-3.1-8b-instant" # model or app_config.model or 
        
        if not self.model:
            raise ValueError("Model name is required but not provided")
            
        # Get API key from environment variable
        self.api_key = os.getenv("GROQ_API_KEY", None)
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
            
        try:
            # Initialize ChatGroq LLM
            self.llm = ChatGroq(
                model=self.model,
                api_key=self.api_key,
                temperature=0.5,
                max_tokens=300,
                top_p=0.95
            )
        except Exception as e:
            print(f"Warning: Could not initialize Groq with model '{self.model}': {e}")
            # Fallback to a common model
            self.model = "llama-3.1-8b-instant"
            self.llm = ChatGroq(
                model=self.model,
                api_key=self.api_key,
                temperature=0.5,
                max_tokens=300,
                top_p=0.95
            )
    
    def chat(self, messages: list[dict], system_prompt: Optional[str] = None) -> str:
        """
        Main chat function using Groq
        
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
            return response.content
        except Exception as e:
            print(f"Error in Groq chat_simple: {e}")
            return f"I encountered an error: {str(e)}"

    def bind_tools(self, tools: list[dict]):
        """
        Bind tools to the LLM
        """
        self.llm = self.llm.bind_tools(tools)
        return self.llm


# Legacy function for backward compatibility
def call_groq_model(
    messages: list[dict], 
    system_prompt: Optional[str], 
    model: str,
    temperature: float = 0.5,
    max_tokens: int = 300,
    top_p: float = 0.95,
    stop: list = None):
    """
    Legacy function - use GroqClient class instead
    """
    client = GroqClient(model=model)
    client.llm.temperature = temperature
    client.llm.max_tokens = max_tokens
    client.llm.top_p = top_p
    if stop:
        client.llm.stop = stop
    
    return client.chat(messages, system_prompt)