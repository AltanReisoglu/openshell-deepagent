"""OpenShell Deep Agent with AI-Q Blueprint Logic.

General-purpose coding and analysis agent using OpenShell and the NVIDIA AI-Q Planner/Researcher pattern.
"""

import os
import yaml
from datetime import datetime
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

from src.backend import create_backend
from src.prompts import (
    ORCHESTRATOR_INSTRUCTIONS,
    PLANNER_INSTRUCTIONS,
    RESEARCHER_INSTRUCTIONS,
)

current_date = datetime.now().strftime("%Y-%m-%d")

# 1. Load configuration from AI-Q style yaml
config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

def load_llm(name: str):
    """Helper to instantiate LLMs based on YAML config using init_chat_model."""
    llm_conf = config["llms"][name]
    return init_chat_model(
        llm_conf["model_name"],
        temperature=llm_conf.get("temperature", 0.1)
    )

agent_conf = config["functions"]["deep_research_agent"]

# Initialize models according to roles
orchestrator_llm = load_llm(agent_conf["orchestrator_llm"])
planner_llm = load_llm(agent_conf["planner_llm"])
researcher_llm = load_llm(agent_conf["researcher_llm"])

# 2. Define Subagents explicitly to mitigate context length bloat (Lost-in-the-middle)
subagents = [
    {
        "name": "planner-agent",
        "description": "Content-driven planning. Interleaves reasoning to build test plans and outlines. Call this FIRST.",
        "system_prompt": PLANNER_INSTRUCTIONS.format(date=current_date),
        "model": planner_llm,
    },
    {
        "name": "researcher-agent",
        "description": "Executes coding logic, tests outputs, and runs sandbox operations according to the planner.",
        "system_prompt": RESEARCHER_INSTRUCTIONS.format(date=current_date),
        "model": researcher_llm,
    }
]

# 3. Build the core Orchestrator Agent
agent = create_deep_agent(
    model=orchestrator_llm,
    system_prompt=ORCHESTRATOR_INSTRUCTIONS.format(date=current_date),
    memory=["/memory/AGENTS.md"],
    backend=create_backend,
    subagents=subagents,
)
