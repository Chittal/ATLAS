from langchain.llms import Ollama
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
)
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)
from typing import Optional


def call_ollama_model(model: str, messages: list[dict], system_prompt: Optional[str]):
	"""
	This function calls the ollama model with provided messages.
	"""
    llm = Ollama(model=model)

    chat_messages = []

    # Add system message if provided
    if system_prompt:
        chat_messages.append(SystemMessage(content=system_prompt))
    
    for msg in messages:
		if "ai"	in msg and msg["ai"]:
        	chat_messages.append(AIMessage(content=msg["ai"]))
		# Add user message
		if "user" in msg and msg["user"]:
			chat_messages.append(HumanMessage(content=msg["user"]))
    

    # Send the message to the model
    response = llm.invoke(chat_messages)
    return response.content
