import json
from config import app_config
# from llm.ollama import OllamaClient
from llm.bedrock import BedrockClient
# from llm.litellm import LiteLLMClient
from schemas.agent import AgentState
from langchain_core.tools import tool as langchain_tool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from helper.kuzu_db_helper import KuzuSkillGraph

class PersonalizedRoutePlanningAgent:
    def __init__(self, kuzu_helper: KuzuSkillGraph | None = None):
        # Initialize config instance and use it for OllamaClient

        # self.llm = OllamaClient(model=app_config.model)
        # self.llm = LiteLLMClient(model=app_config.model)
        self.llm = BedrockClient(model=app_config.model)
        # Use injected shared instance if provided; otherwise, create one
        self.kuzu_db_helper = kuzu_helper if kuzu_helper is not None else KuzuSkillGraph()
        # tools = [self.pre_requisite, self.skill_details]
        # self.llm.bind_tools(tools)
    
    def prerequisite(self, state: AgentState):
        print("I AM AT PRE-REQUISITE=============")
        print("State", state)
        if state["category"] != "PREREQUISITE":
            return state
        target_skill = state["target_skill"]
        prerequisites = self.kuzu_db_helper.get_skill_prerequisites_by_name(target_skill)
        if prerequisites:
            prerequisites = [prerequisite["name"] for prerequisite in prerequisites]
            prerequisites = ", ".join(prerequisites)
        else:
            prerequisites = "No prerequisites found"
        print("Prerequisites IN DATABASE===========", prerequisites)
        prompt = f"""
        You are a helpful assistant that provides the prerequisites for a given skill.
        I will provide you with a list of prerequisites already in the database for the target skill.
        - Prerequisites_in_database: {prerequisites}
        - Target skill: {target_skill}
        - The list can be skills separated by commas, or none.
        Your task:
        - Return the prerequisites in a friendly and concise format.
        - If Prerequisites_in_database is none, generate a meaningful list of relevant prerequisites for the target skill.
        - If Prerequisites_in_database is not none, reformat them in a user-friendly way.
        Do not include any extra text—only the list of prerequisites.
        """
        response = self.llm.chat_simple(prompt)
        state["step"] = "prerequisite"
        state["status"] = "success"
        state["messages"].append({"role": "assistant", "content": response})
        return state
    
    # @langchain_tool
    # def skill_details(self, state: AgentState):
    #     print("I AM AT SKILL DETAILS=============")
    #     target_skill = state["target_skill"]
    #     skill_details = self.kuzu_db_helper.get_skill_details_by_name(target_skill)
    #     if skill_details:
    #         skill_details = skill_details["details"]
    #     else:
    #         skill_details = "No skill details found"
    #     prompt = f"""
    #     You are a helpful assistant that answers general queries.
    #     User message: {{"current_message": {state["current_message"]}, "category": {state["category"]}}}
    #     Generate a Kuzu DB Cypher query to fetch the information user is asking for.
    #     Return the answer in friendly and concise format without any other text.
    #     """
    #     response = self.llm.chat_simple(prompt)
    #     state["step"] = "skill_details"
    #     state["status"] = "success"
    #     return state

    def classify_query(self, state: AgentState):
        try:
            print("I AM AT CLASSIFY QUERY=============")
            # - SKILL_DETAILS: What is the details of this skill?, what is a skill? "SKILL_DETAILS" | 
            prompt = f"""
            You are a helpful assistant that classifies user message into one of the following categories:
                - ROUTE_PLANNING: If the user message is about finding the path between two skills or I know this skill, I want to learn other skill.
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
            response = self.llm.chat_simple(prompt)
            response = json.loads(response)
            print("CATEGORY===========", response["category"])
            state["category"] = response["category"].upper()
            state["step"] = "classify_query"
            state["status"] = "success"
            return state
        except Exception as e:
            print("CLASSIFY QUERY ERROR===========", e)
            state["step"] = "classify_query"
            state["status"] = "error"
            state["error"] = str(e)
            return state

    def extract_skill_name(self, state: AgentState):
        # try:
        print("I AM AT EXTRACT SKILL NAME=============")
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

        Input: {{"user_message": "What is the details of Python?", "category": "SKILL_DETAILS"}}
        Output: {{"target_skill": "Python"}}

        Now extract skills from the following:
        Input: {{"user_message": "{state["current_message"]}", "category": "{state["category"]}"}}

        Output must be JSON with no additional text. Do not include ```json or ``` in the output.
        """
        response = self.llm.chat_simple(prompt)
        print("RESPONSE===========", response)
        response = json.loads(response)
        start_skill = response.get("start_skill", None)
        target_skill = response.get("target_skill", None)
        if start_skill:
            start_skill = start_skill.lower()
        if target_skill:
            target_skill = target_skill.lower()
        state["start_skill"] = start_skill
        print("START SKILL===========", state["start_skill"])
        state["target_skill"] = target_skill
        print("TARGET SKILL===========", state["target_skill"])
        state["step"] = "extract_skill_name"
        state["status"] = "success"
        return state
        # except Exception as e:
        #     print("ERROR===========", e)
        #     state["step"] = "extract_skill_name"
        #     state["status"] = "error"
        #     state["error"] = str(e)
        #     return state
    
    def route_planning(self, state: AgentState):
        print("I AM AT ROUTE PLANNING=============")
        try:
            print("State", state)
            if state["category"] != "ROUTE_PLANNING":
                return state
            target_skill = state["target_skill"]
            start_skill = state["start_skill"]
            path_objects = self.kuzu_db_helper.find_learning_path(start_skill, target_skill)
            
            # Store the original path objects for highlighting
            state["path_objects"] = path_objects
            
            if path_objects:
                path_names = [p["name"] for p in path_objects]
                path = ", ".join(path_names)
            else:
                path = "No path found"
            print("Path IN DATABASE===========", path)
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
            response = self.llm.chat_simple(prompt)
            state["step"] = "route_planning"
            state["status"] = "success"
            state["messages"].append({"role": "assistant", "content": response})
            return state
        except Exception as e:
            state["step"] = "route_planning"
            state["status"] = "error"
            state["error"] = str(e)
            return state

    def general_query(self, state: AgentState):
        try:
            print("I AM AT GENERAL QUERY=============")
            prompt = f"""
            You are a helpful assistant that answers general queries.
            User message: {{"current_message": {state["current_message"]}, "category": {state["category"]}}}
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
            if category == "ROUTE_PLANNING":
                return "route_planning"
            elif category == "PREREQUISITE":
                return "prerequisite"
            else:
                return "general_query"
        print("creating graph")
        graph = StateGraph(AgentState)

        graph.add_node("classify_query", self.classify_query)
        graph.add_node("general_query", self.general_query)
        graph.add_node("extract_skill_name", self.extract_skill_name)
        graph.add_node("route_planning", self.route_planning)
        graph.add_node("prerequisite", self.prerequisite)
        # graph.add_node("skill_details", self.skill_details)
        graph.add_edge(START, "classify_query")
        graph.add_edge("classify_query", "extract_skill_name")
        graph.add_conditional_edges(
            "extract_skill_name",
            map_category_to_node,
            {"end": END, "general_query": "general_query", "prerequisite": "prerequisite", "route_planning": "route_planning"} # , "skill_details": "skill_details"
        )
        graph.add_edge("general_query", END)
        graph.add_edge("route_planning", END)
        graph.add_edge("prerequisite", END)
        # graph.add_edge("skill_details", END)
        graph = graph.compile()
        initial_state = {
            "current_message": user_message,
            "messages": [],
            "status": "start",
            "step": "classify_query",
            "is_complete": False,
            "metadata": {},
            "category": None,
            "start_skill": None,
            "target_skill": None,
            "path_objects": []
        }
        print(initial_state, "initial_state")
        result = graph.invoke(initial_state)
        print(result, "result")
        return result

