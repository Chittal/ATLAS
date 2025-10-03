from calendar import c
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import Optional

import os

	
def call_groq_model(
	messages: list[dict], 
	system_prompt: Optional[str], 
	model: str,
	temperature: float = 0.5,
    max_tokens: int = 300,
    top_p: float = 0.95,
    stop: list = None):
	"""
	This function calls the Groq model with provided messages.
	"""

	# Get API key from environment variable
	api_key = os.getenv("GROQ_API_KEY", None)

	# Initialize the Groq model
	llm = ChatGroq(
		model=model,  # Use the prompt as the model name
		api_key=api_key,
		temperature=temperature,
		max_tokens=max_tokens,
		top_p=top_p,
		stop=stop
	)

	chat_messages = []

	# Add system message if provided
	if system_prompt:
		chat_messages.append(SystemMessage(content=system_prompt))

	for msg in messages:
		if msg["role"] == "ai":
			chat_messages.append(AIMessage(content=msg["content"]))
		# Add user message
		if msg["role"] == "user":
			chat_messages.append(HumanMessage(content=msg["content"]))

	# Send the message to the model
	response = llm.invoke(chat_messages)
	# print(response, "response")
	return response.content