"""
Configuration for AgentCore deployment
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class AgentConfig(BaseSettings):
    """Configuration for the personalized route planning agent"""
    
    # LLM Configuration
    llm_provider: str = Field(default="bedrock", description="LLM provider to use")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Bedrock model to use")
    
    # AWS Bedrock Configuration
    aws_region: str = Field(default="us-east-1", description="AWS region for Bedrock")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret access key")
    bedrock_model_id: str = Field(default="anthropic.claude-3-5-sonnet-20241022-v2:0", description="Bedrock model ID")
    
    # Temperature and other model parameters
    temperature: float = Field(default=0.7, description="Model temperature")
    max_tokens: int = Field(default=1000, description="Maximum tokens to generate")
    
    # Render App API Configuration
    render_app_url: str = Field(description="URL of the main Render app")
    
    # AgentCore Configuration
    agentcore_environment: str = Field(default="production", description="AgentCore environment")
    agent_id: Optional[str] = Field(default=None, description="Agent ID in AgentCore")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_timeout: int = Field(default=30, description="API timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global config instance
agent_config = AgentConfig()
