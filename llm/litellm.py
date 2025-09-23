import openai
import os
from dotenv import load_dotenv
from typing import Optional
load_dotenv()  # take environment variables from .env.

api_key = os.getenv("LITELLM_API_KEY")
client = openai.OpenAI(
	api_key=api_key,
	base_url="https://apps.reknew.ai/litellm"
)

import base64

# Helper function to encode images to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def chat_completions_openai(messages, model="reasoning_mini"):
    # Example with text only
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    print(response.choices[0].message.content.split("</think>")[-1].lstrip())


    return response.choices[0].message.content.split("</think>")[-1].lstrip()


from langchain_litellm import ChatLiteLLM
from langchain.schema import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)

api_key = os.getenv("LITELLM_API_KEY")
api_base = os.getenv("LITELLM_API_BASE")
llm_provider = os.getenv("LITELLM_LLM_PROVIDER")

def chat_completions(messages: list[dict], system_prompt: Optional[str], model: str = "falcon3-1b"):
    """
    api base is for litellm provider and base_url is for openai provider
    """
    llm = ChatLiteLLM(model=model, api_base=api_base, api_key=api_key, custom_llm_provider=llm_provider)

    chat_messages=[]

    # Add system message if provided
    if system_prompt:
        chat_messages.append(SystemMessage(content=system_prompt))
    
    for msg in messages:
        if "ai" in msg and msg["ai"]:
            chat_messages.append(AIMessage(content=msg["ai"]))
        # Add user message
        if "user" in msg and msg["user"]:
            chat_messages.append(HumanMessage(content=msg["user"]))
    

    # Send the message to the model
    response = llm.invoke(chat_messages)
    print("LLM response:", response.content)
    return response