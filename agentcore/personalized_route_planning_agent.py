"""
Personalized Route Planning Agent for AgentCore deployment
"""
import json
import asyncio
from typing import Dict, List, Any, Optional
from langchain_core.tools import tool as langchain_tool
from langgraph.graph import StateGraph, START, END

from config import agent_config
from api_client import render_client
from llm_client import get_llm_client
from schemas import AgentState, AgentRequest, AgentResponse
import structlog

logger = structlog.get_logger()

class PersonalizedRoutePlanningAgent:
    """Personalized Route Planning Agent for AgentCore"""
    
    def __init__(self):
        """Initialize the agent"""
        self.llm = get_llm_client()
        self.api_client = render_client
        
        # Initialize the graph
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph execution graph"""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("classify_query", self.classify_query)
        graph.add_node("extract_skill_name", self.extract_skill_name)
        graph.add_node("route_planning", self.route_planning)
        graph.add_node("prerequisite", self.prerequisite)
        graph.add_node("general_query", self.general_query)
        
        # Add edges
        graph.add_edge(START, "classify_query")
        graph.add_edge("classify_query", "extract_skill_name")
        graph.add_conditional_edges(
            "extract_skill_name",
            self._map_category_to_node,
            {
                "general_query": "general_query",
                "prerequisite": "prerequisite", 
                "route_planning": "route_planning"
            }
        )
        graph.add_edge("general_query", END)
        graph.add_edge("route_planning", END)
        graph.add_edge("prerequisite", END)
        
        return graph.compile()
    
    def _map_category_to_node(self, state: AgentState) -> str:
        """Map category to the appropriate node"""
        category = state["category"]
        if category == "ROUTE_PLANNING":
            return "route_planning"
        elif category == "PREREQUISITE":
            return "prerequisite"
        else:
            return "general_query"
    
    async def classify_query(self, state: AgentState) -> AgentState:
        """Classify the user query"""
        try:
            logger.info("Classifying query", message=state["current_message"])
            
            prompt = f"""
            You are a helpful assistant that classifies user message into one of the following categories:
                - ROUTE_PLANNING: If the user message is about finding the path between two skills or "I know this skill, I want to learn other skill".
                - PREREQUISITE: What are the prerequisites for this skill?, What should I learn before this skill?
                - GENERAL_QUERY: If the user message is not about the above categories, return "GENERAL_QUERY".

            User message: {state["current_message"]}

            Return the category in JSON format including the category, confidence score, and reasoning. Provide in below format ONLY:
            {{
                "category": "ROUTE_PLANNING" | "PREREQUISITE" | "GENERAL_QUERY",
                "confidence_score": 0.0 to 1.0,
                "reasoning": "Reasoning for the classification"
            }}
            """
            
            response = await self.llm.chat_simple(prompt)
            response_data = json.loads(response)
            
            state["category"] = response_data["category"].upper()
            state["step"] = "classify_query"
            state["status"] = "success"
            
            logger.info("Query classified", category=state["category"])
            return state
            
        except Exception as e:
            logger.error("Classification error", error=str(e))
            state["step"] = "classify_query"
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    async def extract_skill_name(self, state: AgentState) -> AgentState:
        """Extract skill names from the query"""
        try:
            logger.info("Extracting skill names", category=state["category"])
            
            if state["category"] not in ["PREREQUISITE", "ROUTE_PLANNING"]:
                return state
            
            prompt = f"""
            You are a skill extraction assistant. Extract skills based on the category provided.

            RULES:
            1. If category is "PREREQUISITE": Extract only the target skill (the skill being asked about)
            2. If category is "ROUTE_PLANNING": Extract both start_skill (current skill/role) and target_skill (desired skill)
            3. Return ONLY valid JSON, no additional text
            4. Skill names should be in title case
            5. If a skill is not found, use null

            OUTPUT FORMAT:
            - For PREREQUISITE: {{"target_skill": "skill_name"}}
            - For ROUTE_PLANNING: {{"start_skill": "skill_name", "target_skill": "skill_name"}}

            EXAMPLES:

            Input: {{"user_message": "What are the prerequisites of Python?", "category": "PREREQUISITE"}}
            Output: {{"target_skill": "Python"}}

            Input: {{"user_message": "What should I learn before I start learning Python?", "category": "PREREQUISITE"}}
            Output: {{"target_skill": "Python"}}

            Input: {{"user_message": "I am a data engineer I want to learn ai agents", "category": "ROUTE_PLANNING"}}
            Output: {{"start_skill": "Data Engineer", "target_skill": "AI Agents"}}

            Input: {{"user_message": "I know only basics of coding I want to learn Python", "category": "ROUTE_PLANNING"}}
            Output: {{"start_skill": "Basics of Coding", "target_skill": "Python"}}

            Now extract skills from the following:
            Input: {{"user_message": "{state["current_message"]}", "category": "{state["category"]}"}}

            Output must be JSON with no additional text. Do not include ```json or ``` in the output.
            """
            
            response = await self.llm.chat_simple(prompt)
            response_data = json.loads(response)
            
            start_skill = response_data.get("start_skill", None)
            target_skill = response_data.get("target_skill", None)
            
            if start_skill:
                start_skill = start_skill.lower()
            if target_skill:
                target_skill = target_skill.lower()
                
            state["start_skill"] = start_skill
            state["target_skill"] = target_skill
            state["step"] = "extract_skill_name"
            state["status"] = "success"
            
            logger.info("Skills extracted", start_skill=start_skill, target_skill=target_skill)
            return state
            
        except Exception as e:
            logger.error("Skill extraction error", error=str(e))
            state["step"] = "extract_skill_name"
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    async def prerequisite(self, state: AgentState) -> AgentState:
        """Handle prerequisite queries"""
        try:
            logger.info("Handling prerequisite query", target_skill=state["target_skill"])
            
            if state["category"] != "PREREQUISITE":
                return state
            
            target_skill = state["target_skill"]
            
            # Get prerequisites from the main app
            prerequisites = await self.api_client.get_skill_prerequisites(target_skill)
            
            if prerequisites:
                prerequisites_list = [prerequisite["name"] for prerequisite in prerequisites]
                prerequisites_text = ", ".join(prerequisites_list)
            else:
                prerequisites_text = "No prerequisites found"
            
            logger.info("Prerequisites retrieved", prerequisites=prerequisites_text)
            
            prompt = f"""
            You are a helpful assistant that provides the prerequisites for a given skill.
            I will provide you with a list of prerequisites already in the database for the target skill.
            - Prerequisites_in_database: {prerequisites_text}
            - Target skill: {target_skill}
            - The list can be skills separated by commas, or none.
            Your task:
            - Return the prerequisites in a friendly and concise format.
            - If Prerequisites_in_database is none, generate a meaningful list of relevant prerequisites for the target skill.
            - If Prerequisites_in_database is not none, reformat them in a user-friendly way.
            Do not include any extra text—only the list of prerequisites.
            """
            
            response = await self.llm.chat_simple(prompt)
            
            state["step"] = "prerequisite"
            state["status"] = "success"
            state["messages"].append({"role": "assistant", "content": response})
            
            logger.info("Prerequisite response generated")
            return state
            
        except Exception as e:
            logger.error("Prerequisite error", error=str(e))
            state["step"] = "prerequisite"
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    async def route_planning(self, state: AgentState) -> AgentState:
        """Handle route planning queries"""
        try:
            logger.info("Handling route planning query", 
                       start_skill=state["start_skill"], 
                       target_skill=state["target_skill"])
            
            if state["category"] != "ROUTE_PLANNING":
                return state
            
            target_skill = state["target_skill"]
            start_skill = state["start_skill"]
            
            # Get learning path from the main app
            path_objects = await self.api_client.find_learning_path(start_skill, target_skill)
            
            # Store the original path objects for highlighting
            state["path_objects"] = path_objects
            
            if path_objects:
                path_names = [p["name"] for p in path_objects]
                path = ", ".join(path_names)
            else:
                path = "No path found"
            
            logger.info("Learning path retrieved", path=path)
            
            prompt = f"""
            Given this learning path from {start_skill} to {target_skill}:
            {path}
            - Path is a list of skills separated by commas. 
            - It will include the start and target skill.
            Create a friendly, motivating curriculum outline that:
            - Leave out the start skill and create progression for all other skills.
            - Shows progression clearly
            - Estimates time per stage
            - Explains why each step matters
            - Keeps it encouraging and actionable
            Do not include any extra text—only the list of prerequisites.
            """
            
            response = await self.llm.chat_simple(prompt)
            
            state["step"] = "route_planning"
            state["status"] = "success"
            state["messages"].append({"role": "assistant", "content": response})
            
            logger.info("Route planning response generated")
            return state
            
        except Exception as e:
            logger.error("Route planning error", error=str(e))
            state["step"] = "route_planning"
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    async def general_query(self, state: AgentState) -> AgentState:
        """Handle general queries"""
        try:
            logger.info("Handling general query")
            
            prompt = f"""
            You are a helpful assistant that answers general queries.
            User message: {{"current_message": {state["current_message"]}, "category": {state["category"]}}}
            Return the answer in friendly and concise format without any other text.
            """
            
            response = await self.llm.chat_simple(prompt)
            
            state["step"] = "general_query"
            state["status"] = "success"
            state["messages"].append({"role": "assistant", "content": response})
            
            logger.info("General query response generated")
            return state
            
        except Exception as e:
            logger.error("General query error", error=str(e))
            state["step"] = "general_query"
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Execute the agent with a request"""
        try:
            logger.info("Executing agent", message=request["message"])
            
            # Check if main app is healthy
            is_healthy = await self.api_client.health_check()
            if not is_healthy:
                logger.warning("Main app is not healthy")
            
            # Initialize state
            initial_state = {
                "current_message": request["message"],
                "messages": [],
                "status": "start",
                "step": "classify_query",
                "is_complete": False,
                "metadata": request.get("metadata", {}),
                "category": None,
                "start_skill": None,
                "target_skill": None,
                "path_objects": []
            }
            
            # Execute the graph
            result = await self.graph.ainvoke(initial_state)
            
            # Extract the final message
            final_message = ""
            if result["messages"]:
                final_message = result["messages"][-1]["content"]
            
            response = {
                "message": final_message,
                "status": result["status"],
                "category": result["category"],
                "path_objects": result.get("path_objects", []),
                "error": result.get("error"),
                "metadata": result["metadata"]
            }
            
            logger.info("Agent execution completed", status=result["status"])
            return response
            
        except Exception as e:
            logger.error("Agent execution error", error=str(e))
            return {
                "message": "I apologize, but I encountered an error processing your request.",
                "status": "error",
                "category": "GENERAL_QUERY",
                "path_objects": [],
                "error": str(e),
                "metadata": {}
            }

# Global agent instance
agent = PersonalizedRoutePlanningAgent()
