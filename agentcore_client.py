"""
AgentCore client for communicating with the deployed agent
"""
import httpx
import asyncio
import json
from typing import Dict, Any, Optional
import structlog
import os
from dotenv import load_dotenv

load_dotenv()

logger = structlog.get_logger()

class AgentCoreClient:
    """Client for communicating with AgentCore deployed agent"""
    
    def __init__(self):
        self.agentcore_url = os.getenv("AGENTCORE_URL")
        self.agentcore_api_key = os.getenv("AGENTCORE_API_KEY")
        self.timeout = 30
        self.max_retries = 3
        
        # Set up headers
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Learning-Map-App/1.0"
        }
        
        if self.agentcore_api_key:
            self.headers["Authorization"] = f"Bearer {self.agentcore_api_key}"
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        if not self.agentcore_url:
            raise Exception("AgentCore URL not configured")
            
        url = f"{self.agentcore_url.rstrip('/')}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self.headers,
                        json=data,
                        params=params
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    else:
                        logger.warning(
                            "AgentCore request failed",
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            url=url
                        )
                        
                        if attempt == self.max_retries - 1:
                            raise Exception(f"AgentCore request failed: {response.status_code} - {response.text}")
                            
            except Exception as e:
                logger.error(
                    "AgentCore request error",
                    error=str(e),
                    attempt=attempt + 1,
                    url=url
                )
                
                if attempt == self.max_retries - 1:
                    raise e
                    
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    async def chat_with_agent(self, message: str, user_id: str = None) -> Dict[str, Any]:
        """Send a chat message to the AgentCore agent"""
        try:
            data = {
                "message": message,
                "user_id": user_id,
                "session_id": f"session_{user_id}" if user_id else "anonymous_session",
                "metadata": {"source": "learning_map_app"}
            }
            
            response = await self._make_request("POST", "/invoke", data=data)
            return response
            
        except Exception as e:
            logger.error("Failed to chat with AgentCore agent", error=str(e))
            raise e
    
    async def health_check(self) -> bool:
        """Check if AgentCore is healthy"""
        try:
            response = await self._make_request("GET", "/health")
            return response.get("status") == "healthy"
        except Exception as e:
            logger.error("AgentCore health check failed", error=str(e))
            return False

# Global client instance
agentcore_client = AgentCoreClient()
