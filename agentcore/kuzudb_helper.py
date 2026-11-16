import logging
from config import app_config
import requests

def get_skill_prerequisites_by_name(skill_name):
    """
    Get the prerequisites for a specific skill from the database.
    The input is the skill name.
    The output is a list of prerequisites for the skill.
    """
    url = f"{app_config.atlas_app_url}/api/skills/{skill_name}/prerequisites"
    logging.debug("%s %s", url, "url")
    logging.debug("%s %s", app_config.atlas_app_url, "app_config.atlas_app_url")
    response = requests.get(url, verify=False)
    logging.debug("%s %s", response, "response")
    response_json = response.json()
    if response.status_code == 200:
        prerequisites = response_json["prerequisites"]
        # prerequisites = [prerequisite["name"] for prerequisite in prerequisites]
        return prerequisites
    return []

def find_learning_path(start_skill, target_skill):
    """
    Find the learning path between two skills from the database.
    The input is the start and target skill names.
    The output is a list of skills in the learning path.
    """
    logging.debug("I AM AT FIND LEARNING PATH=============")
    logging.debug("%s %s", app_config.atlas_app_url, "app_config.atlas_app_url")
    url = f"{app_config.atlas_app_url}/api/skill-path?start={start_skill}&end={target_skill}"
    logging.debug("%s %s", url, "url")
    response = requests.get(url, verify=False)
    logging.debug("%s %s", response, "response")
    response_json = response.json()
    logging.debug("%s %s", response_json, "response_json")
    if response.status_code == 200:
        path = response_json["path"]
        # path = [skill["name"] for skill in path]
        return path
    return []