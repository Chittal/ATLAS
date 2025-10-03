import json
from config import Config
from llm.ollama import OllamaClient
from agents.state import AgentState
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from helper.kuzu_db_helper import KuzuSkillsGraphHelper

class PersonalizedRoutePlanningAgent:
    def __init__(self):
        # Initialize config instance and use it for OllamaClient
        config_instance = Config()
        self.llm = OllamaClient(model=config_instance.model)
        kuzu_db_helper = KuzuSkillsGraphHelper()
        tools = [kuzu_db_helper.find_learning_path, kuzu_db_helper.get_skill_prerequisites_by_name]
        self.llm.bind_tools(tools)
    
    def classify_query(self, state: AgentState):
        try:
            prompt = f"""
            You are a helpful assistant that classifies user message into one of the following categories:
                - ROUTE_PLANNING: If the user message is about finding the path between two skills or I know this skill, I want to learn other skill.
                - PREREQUISITE: What are the prerequisites for this skill?, What should I learn before this skill?
                - SKILL_DETAILS: What is the details of this skill?, what is a skill?
                - GENERAL_QUERY: If the user message is not about the above categories, return "GENERAL_QUERY".

            User message: {state["current_message"]}

            Return the category in json format including the category, confidence score, and reasoning. Provide in below format ONLY:
            {{
                "category": "ROUTE_PLANNING" | "PREREQUISITE" | "SKILL_DETAILS" | "GENERAL_QUERY",
                "confidence_score": 0.0 to 1.0,
                "reasoning": "Reasoning for the classification"
            }}
            """
            response = self.llm.chat_simple(prompt)
            response = json.loads(response)
            print("CATEGORY===========", response["category"])
            state["category"] = response["category"]
            state["step"] = "classify_query"
            state["status"] = "success"
            return state
        except Exception as e:
            state["step"] = "classify_query"
            state["status"] = "error"
            state["error"] = str(e)
            return state

    def extract_skill_name(self, state: AgentState):
        try:
            prompt = f"""
            You are a skill extraction assistant. Extract skills based on the category provided.

            RULES:
            1. If category is "PREREQUISITE" or "SKILL_DETAILS": Extract only the target skill (the skill being asked about)
            2. If category is "ROUTE_PLANNING": Extract both start_skill (current skill/role) and target_skill (desired skill)
            3. Return ONLY valid JSON, no additional text
            4. Skill names should be in title case
            5. If a skill is not found, use null

            OUTPUT FORMAT:
            - For PREREQUISITE/SKILL_DETAILS: {"target_skill": "skill_name"}
            - For ROUTE_PLANNING: {"start_skill": "skill_name", "target_skill": "skill_name"}

            EXAMPLES:

            Input: {"user_message": "What are the prerequisites of Python?", "category": "PREREQUISITE"}
            Output: {"target_skill": "Python"}

            Input: {"user_message": "What should I learn before I start learning Python?", "category": "PREREQUISITE"}
            Output: {"target_skill": "Python"}

            Input: {"user_message": "I am a data engineer I want to learn ai agents", "category": "ROUTE_PLANNING"}
            Output: {"start_skill": "Data Engineer", "target_skill": "AI Agents"}

            Input: {"user_message": "I know only basics of coding I want to learn Python", "category": "ROUTE_PLANNING"}
            Output: {"start_skill": "Basics of Coding", "target_skill": "Python"}

            Input: {"user_message": "What is the details of Python?", "category": "SKILL_DETAILS"}
            Output: {"target_skill": "Python"}

            Now extract skills from the following:
            Input: {{"user_message": "{state["current_message"]}", "category": "{state["category"]}"}}
            Output:
            """
            response = self.llm.chat_simple(prompt)
            response = json.loads(response)
            print("RESPONSE===========", response)
            state["start_skill"] = response["start_skill"]
            state["target_skill"] = response["target_skill"]
            state["step"] = "extract_skill_name"
            state["status"] = "success"
            return state
        except Exception as e:
            state["step"] = "extract_skill_name"
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    def prerequisite(self, state: AgentState):
        print("I AM AT PRE-REQUISITE=============")
        try:
            prompt = f"""
            You are a helpful assistant that classifies user message into one of the following categories:
                - ROUTE_PLANNING: If the user message is about finding the path between two skills or I know this skill, I want to learn other skill.
                - PREREQUISITE: What are the prerequisites for this skill?
                - GENERAL_QUERY: If the user message is not about the above categories, return "GENERAL_QUERY".

            User message: {state["current_message"]}

            Return the category in json format including the category, confidence score, and reasoning. Provide in below format ONLY:
            {{
                "category": "ROUTE_PLANNING" | "PREREQUISITE" | "GENERAL_QUERY",
                "confidence_score": 0.0 to 1.0,
                "reasoning": "Reasoning for the classification"
            }}
            """
            response = self.llm.chat_simple(prompt)
            response = json.loads(response)
            print("CATEGORY===========", response["category"], "hjjj")
            state["category"] = response["category"]
            state["step"] = "classify_query"
            state["status"] = "success"
            return state
        except Exception as e:
            state["step"] = "classify_query"
            state["status"] = "error"
            state["error"] = str(e)
            return state
    
    def route_planning(self, state: AgentState):
        print("I AM AT ROUTE PLANNING=============")
        try:
            prompt = f"""
            You are a helpful assistant that classifies user message into one of the following categories:
                - ROUTE_PLANNING: If the user message is about finding the path between two skills or I know this skill, I want to learn other skill.
                - PREREQUISITE: What are the prerequisites for this skill?, What should I learn before this skill?
                - SKILL_DETAILS: What is the details of this skill?, what is a skill?
                - GENERAL_QUERY: If the user message is not about the above categories, return "GENERAL_QUERY".

            User message: {state["current_message"]}

            Return the category in json format including the category, confidence score, and reasoning. Provide in below format ONLY:
            {{
                "category": "ROUTE_PLANNING" | "PREREQUISITE" | "SKILL_DETAILS" | "GENERAL_QUERY",
                "confidence_score": 0.0 to 1.0,
                "reasoning": "Reasoning for the classification"
            }}
            """
            response = self.llm.chat_simple(prompt)
            response = json.loads(response)
            print("CATEGORY===========", response["category"], "hjjj")
            state["category"] = response["category"]
            state["step"] = "classify_query"
            state["status"] = "success"
            return state
        except Exception as e:
            state["step"] = "classify_query"
            state["status"] = "error"
            state["error"] = str(e)
            return state

    def general_query(self, state: AgentState):
        try:
            print("I AM HERE=============")
            prompt = f"""
            You are a helpful assistant that answers general queries.
            User message: {state["current_message"]}
            Return the answer in friendly and concise format without any other text.
            """
            response = self.llm.chat_simple(prompt)
            state["step"] = "general_query"
            state["status"] = "success"
            state["messages"].append({"role": "assistant", "content": response})
            return state
        except Exception as e:
            state["step"] = "general_query"
            state["status"] = "error"
            state["error"] = str(e)
            return state

    def execute_graph(self, user_message):
        def map_category_to_node(state: AgentState):
            print("I AM AT MAP CATEGORY TO NODE=============")
            category = state["category"]
            if category == "GENERAL_QUERY":
                return "general_query"
            elif category == "ROUTE_PLANNING":
                return "route_planning"
            elif category == "PREREQUISITE":
                return "prerequisite"
            else:
                return "general_query"
        print("creating graph")
        graph = StateGraph(AgentState)

        graph.add_node("classify_query", self.classify_query)
        graph.add_node("general_query", self.general_query)
        graph.add_node("route_planning", self.route_planning)
        graph.add_node("prerequisite", self.prerequisite)
        graph.add_edge(START, "classify_query")
        graph.add_conditional_edges(
            "classify_query",
            map_category_to_node,
            {"end": END, "general_query": "general_query", "route_planning": "route_planning", "prerequisite": "prerequisite"}
        )
        graph.add_edge("general_query", END)
        graph.add_edge("route_planning", END)
        graph.add_edge("prerequisite", END)
        graph = graph.compile()
        initial_state = {
            "current_message": user_message,
            "messages": [],
            "status": "start",
            "step": "classify_query",
            "is_complete": False,
            "metadata": {}
        }
        print(initial_state, "initial_state")
        result = graph.invoke(initial_state)
        print(result, "result")
        return result

