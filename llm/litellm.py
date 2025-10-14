from typing import Optional
from langchain_litellm import ChatLiteLLM
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from config import app_config

class LiteLLMClient:
    """LiteLLM client class for handling LLM interactions"""
    
    def __init__(self, model: str = app_config.model):
        self.api_key = app_config.api_key
        self.api_base = app_config.api_base
        self.llm_provider = app_config.llm_provider
        self.model = model
        # Initialize LangChain LiteLLM
        self.llm = ChatLiteLLM(
            model=model, 
            api_base=self.api_base, 
            api_key=self.api_key, 
            custom_llm_provider=self.llm_provider
        )
    
    def chat(self, messages: list[dict], system_prompt: Optional[str] = None) -> str:
        """
        Main chat function using LangChain LiteLLM
        
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
        print("LLM response:", response.content)
        return response.content

    def chat_simple(self, prompt: str) -> str:
        """
        Main chat function using LangChain LiteLLM
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            LLM response content
        """
        response = self.llm.invoke([HumanMessage(content=prompt)])
        return response.content