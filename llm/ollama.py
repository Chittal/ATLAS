from langchain_ollama import ChatOllama
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from typing import Optional
from config import app_config


class OllamaClient:
    """Ollama client class for handling LLM interactions"""
    
    def __init__(self, model: str = None):
        # Use provided model or fallback to config or default
        self.model = model or app_config.model or "llama3.1:8b"
        
        if not self.model:
            raise ValueError("Model name is required but not provided")
            
        try:
            # Initialize ChatOllama LLM
            self.llm = ChatOllama(model=self.model)
        except Exception as e:
            print(f"Warning: Could not initialize Ollama with model '{self.model}': {e}")
            # Fallback to a common model
            self.model = "llama3.1:8b"
            self.llm = ChatOllama(model=self.model)
    
    def chat(self, messages: list[dict], system_prompt: Optional[str] = None) -> str:
        """
        Main chat function using Ollama
        
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
            print(f"Error in Ollama chat_simple: {e}")
            return f"I encountered an error: {str(e)}"

    def bind_tools(self, tools: list[dict]):
        """
        Bind tools to the LLM
        """
        self.llm = self.llm.bind_tools(tools)
        return self.llm
