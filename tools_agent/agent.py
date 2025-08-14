# tools_agent/agent.py - FULL VERSION with your real estate tools

import os
from langchain_core.runnables import RunnableConfig
from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

# Import your existing real estate tools
from tools_agent.utils.tools import (
    search_properties_tool,
    get_property_details_tool,
    get_market_stats_tool,
    calculate_mortgage_tool,
    get_neighborhood_info_tool,
    create_listing_tool,
    get_user_listings_tool,
    update_listing_tool,
    delete_listing_tool,
    search_listings_tool,
)

UNEDITABLE_SYSTEM_PROMPT = "\nIf you need specific property data or market information that you don't have access to, let the user know and guide them on how to find that information through available tools."

DEFAULT_SYSTEM_PROMPT = (
    "You are Vesty, an AI-powered real estate assistant designed to help users navigate the real estate market with expert guidance and personalized recommendations. "
    "You have access to property search, market analysis, mortgage calculations, neighborhood insights, and listing management tools."
)

class GraphConfigPydantic(BaseModel):
    model_name: Optional[str] = Field(
        default="anthropic:claude-3-5-sonnet-latest",
        metadata={
            "x_oap_ui_config": {
                "type": "select",
                "default": "anthropic:claude-3-5-sonnet-latest",
                "description": "The model to use in all generations",
                "options": [
                    {
                        "label": "Claude Sonnet 4",
                        "value": "anthropic:claude-sonnet-4-0",
                    },
                    {
                        "label": "Claude 3.7 Sonnet",
                        "value": "anthropic:claude-3-7-sonnet-latest",
                    },
                    {
                        "label": "Claude 3.5 Sonnet",
                        "value": "anthropic:claude-3-5-sonnet-latest",
                    },
                    {
                        "label": "Claude 3.5 Haiku",
                        "value": "anthropic:claude-3-5-haiku-latest",
                    },
                    {"label": "o4 mini", "value": "openai:o4-mini"},
                    {"label": "o3", "value": "openai:o3"},
                    {"label": "o3 mini", "value": "openai:o3-mini"},
                    {"label": "GPT 4o", "value": "openai:gpt-4o"},
                    {"label": "GPT 4o mini", "value": "openai:gpt-4o-mini"},
                    {"label": "GPT 4.1", "value": "openai:gpt-4.1"},
                    {"label": "GPT 4.1 mini", "value": "openai:gpt-4.1-mini"},
                ],
            }
        },
    )
    temperature: Optional[float] = Field(
        default=0.1,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 0.1,
                "min": 0,
                "max": 2,
                "step": 0.1,
                "description": "Controls randomness (0 = deterministic, 2 = creative)",
            }
        },
    )
    max_tokens: Optional[int] = Field(
        default=4000,
        metadata={
            "x_oap_ui_config": {
                "type": "number",
                "default": 4000,
                "min": 1,
                "description": "The maximum number of tokens to generate",
            }
        },
    )
    system_prompt: Optional[str] = Field(
        default=DEFAULT_SYSTEM_PROMPT,
        metadata={
            "x_oap_ui_config": {
                "type": "textarea",
                "placeholder": "Enter a system prompt...",
                "description": f"The system prompt to use in all generations. The following prompt will always be included at the end of the system prompt:\n---{UNEDITABLE_SYSTEM_PROMPT}\n---",
                "default": DEFAULT_SYSTEM_PROMPT,
            }
        },
    )

def get_api_key_for_model(model_name: str, config: RunnableConfig):
    """Get API key for the specified model"""
    model_name = model_name.lower()
    model_to_key = {
        "openai:": "OPENAI_API_KEY",
        "anthropic:": "ANTHROPIC_API_KEY", 
        "google": "GOOGLE_API_KEY"
    }
    key_name = next((key for prefix, key in model_to_key.items() 
                    if model_name.startswith(prefix)), None)
    if not key_name:
        return None
    
    # Try to get from config first
    api_keys = config.get("configurable", {}).get("apiKeys", {})
    if api_keys and api_keys.get(key_name) and len(api_keys[key_name]) > 0:
        return api_keys[key_name]
    
    # Fallback to environment variable
    return os.getenv(key_name)

async def graph(config: RunnableConfig):
    """Create the agent graph with real estate tools"""
    cfg = GraphConfigPydantic(**config.get("configurable", {}))
    
    # Initialize all your real estate tools
    tools = [
        search_properties_tool,
        get_property_details_tool,
        get_market_stats_tool,
        calculate_mortgage_tool,
        get_neighborhood_info_tool,
        create_listing_tool,
        get_user_listings_tool,
        update_listing_tool,
        delete_listing_tool,
        search_listings_tool,
    ]

    # Initialize the model with proper API key handling
    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )

    # Create the react agent with your tools
    return create_react_agent(
        prompt=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT,
        model=model,
        tools=tools,
        # Removed config_schema to avoid input_schema error
    )