"""
API client for communicating with the main Render app
"""
import httpx
import json
import asyncio
from typing import Dict, List, Any, Optional
from config import agent_config
import structlog

logger = structlog.get_logger()

class RenderAppClient:
    """Client for communicating with the main Render app"""
    
    def __init__(self):
        self.base_url = agent_config.render_app_url.rstrip('/')
        self.timeout = agent_config.api_timeout
        self.max_retries = agent_config.max_retries
        
        # Set up headers
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "AgentCore-PersonalizedRoutePlanning/1.0"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
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
                            "API request failed",
                            status_code=response.status_code,
                            attempt=attempt + 1,
                            url=url
                        )
                        
                        if attempt == self.max_retries - 1:
                            raise Exception(f"API request failed: {response.status_code} - {response.text}")
                            
            except Exception as e:
                logger.error(
                    "API request error",
                    error=str(e),
                    attempt=attempt + 1,
                    url=url
                )
                
                if attempt == self.max_retries - 1:
                    raise e
                    
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    async def get_all_skills(self) -> List[Dict[str, Any]]:
        """Get all available skills from the main app"""
        try:
            response = await self._make_request("GET", "/api/agent/skills")
            return response.get("skills", [])
        except Exception as e:
            logger.error("Failed to get skills", error=str(e))
            return []
    
    async def get_skill_connections(self) -> List[Dict[str, Any]]:
        """Get skill connections from the main app"""
        try:
            response = await self._make_request("GET", "/api/agent/skill-connections")
            return response.get("connections", [])
        except Exception as e:
            logger.error("Failed to get skill connections", error=str(e))
            return []
    
    async def find_learning_path(self, start_skill: str, target_skill: str) -> List[Dict[str, Any]]:
        """Find learning path between two skills"""
        try:
            data = {
                "start_skill": start_skill,
                "target_skill": target_skill
            }
            response = await self._make_request("POST", "/api/agent/learning-path", data=data)
            return response.get("path", [])
        except Exception as e:
            logger.error("Failed to find learning path", error=str(e))
            return []
    
    async def get_skill_prerequisites(self, skill_name: str) -> List[Dict[str, Any]]:
        """Get prerequisites for a skill"""
        try:
            params = {"skill_name": skill_name}
            response = await self._make_request("GET", "/api/agent/skill-prerequisites", params=params)
            return response.get("prerequisites", [])
        except Exception as e:
            logger.error("Failed to get skill prerequisites", error=str(e))
            return []
    
    async def get_skill_details(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a skill"""
        try:
            params = {"skill_name": skill_name}
            response = await self._make_request("GET", "/api/agent/skill-details", params=params)
            return response.get("skill", None)
        except Exception as e:
            logger.error("Failed to get skill details", error=str(e))
            return None
    
    async def health_check(self) -> bool:
        """Check if the main app is healthy"""
        try:
            response = await self._make_request("GET", "/health")
            return response.get("status") == "healthy"
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False

# Global client instance
render_client = RenderAppClient()
