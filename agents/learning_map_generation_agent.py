"""
learning_map_agent.py

Agent that extracts filenames from the `data/` folder and sends them to an LLM
to request an ordered learning map (beginner -> advanced). The LLM is expected
to return a JSON object with `nodes` and `edges` describing a graph where
nodes are skills/topics and edges indicate progression/order.

This file provides a small CLI function `build_learning_map()` which will:
- scan `data/` for roadmap files (files ending with `_roadmap.json` or `.json`)
- build a prompt describing the task and the list of files
- call the OpenAI API when `OPENAI_API_KEY` environment variable is set
- write the LLM response to `llm_outputs/ordered_map.json`

The code is intentionally minimal and dependency-free except for `requests`
which is only required when calling OpenAI's HTTP API directly. If the API key
is not set, the agent will print the prompt and ask the user to paste back
the LLM response (useful for local testing without keys).
"""

from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

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
    llm = ChatLiteLLM(model=model, 
	api_base=api_base, 
	api_key=api_key, custom_llm_provider=llm_provider)

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


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "llm_outputs")
OUTPUT_PATH = os.path.abspath(os.path.join(OUTPUT_DIR, "ordered_map.json"))


def list_skills(data_dir: str = DATA_DIR) -> List[str]:
	"""Return list of relative filenames (base names) for JSON roadmap files.

	We consider files that end with `_roadmap.json` or just `.json` in the
	provided data directory. Subdirectories are listed with their relative
	paths from `data/`.
	"""
	skills = []
	if not os.path.isdir(data_dir):
		return skills
	
	for root, dirs, filenames in os.walk(data_dir):
		for fn in filenames:
			if fn.lower().endswith(".json"):
				# Extract skill name
				name, _ = os.path.splitext(fn)
				skill = name.split("_")[0].replace("-", " ")
				skills.append(skill)

	skills.sort()
	print(len(skills))
	return skills


def build_prompt(filenames: List[str]) -> str:
	"""Construct the instruction prompt to send to the LLM."""
	prompt = (
		"You are given a list of skills. Each skills corresponds "
		"to a technology. Your task is to propose a combined learning "
		"map that orders the skills/topics from beginner to advanced. Output MUST "
		"be valid list of skills ordered from beginner to advanced. "
		"Order the skills based on what should be learned first and what later. "
		"If two or any number of skills are same level just create list of lists.")

	prompt += "\n\Skills:\n"
	for f in filenames:
		prompt += f"{f}, "

	prompt += (
		"\nOutput must be just list surrounded by square brackets. Requirements for the output:\n"
		"1) Skill should be ordered from beginner to advanced. Surround each skill by double quotes.\n"
		"2) If two or more skills are at same level, add it as list of list. This should be surrounded by square brackets. \n"
		"3) Try to cluster/merge obvious duplicates (for example 'javascript' and 'js' names).\n"
		"4) Do not add etc in the list. Just make sure to include all the 63 skills in final list.\n"
		"5) Make sure output is just list. Do not include extraneous text or markdown; return only the list.\n"
	)

	prompt += "\nReturn ONLY the list of items, separated by commas. Do not include any explanation or extra text."
	return prompt


def save_output(text: str, path: str = OUTPUT_PATH) -> None:
	os.makedirs(os.path.dirname(path), exist_ok=True)
	# Try to parse JSON and pretty-print; if not JSON, save raw text
	try:
		obj = json.loads(text)
		with open(path, "w", encoding="utf-8") as f:
			json.dump(obj, f, indent=2, ensure_ascii=False)
	except Exception:
		with open(path, "w", encoding="utf-8") as f:
			f.write(text)


def build_learning_map() -> Dict[str, Any]:
	"""Main entry: list files, build prompt, call LLM (or ask user), and save result.

	Returns the parsed JSON (or raw string under 'raw' key) on success.
	"""
	skills = list_skills()
	prompt = build_prompt(skills)
	print("=== Prompt ===")
	print(prompt)

	# text = chat_completions(messages=[{"role": "system", "content": prompt}])
	text = chat_completions(messages=[], system_prompt=prompt)
	# save
	save_output(text)
	# try to parse
	try:
		result = json.loads(text)
		return result
	except Exception:
		return {"raw": text}


# if __name__ == "__main__":
print("Running learning_map_agent: building learning map from data/ ...")
res = build_learning_map()
print("Result saved to", OUTPUT_PATH)
# print a summary
if isinstance(res, dict) and "nodes" in res:
	print(f"Parsed map with {len(res['nodes'])} nodes and {len(res.get('edges', []))} edges")
else:
	print("Output saved but could not parse JSON automatically.")

