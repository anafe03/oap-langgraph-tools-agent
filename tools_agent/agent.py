import os
from langchain_core.runnables import RunnableConfig
from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

# Import market tools with error handling
try:
    from tools_agent.utils.tools.market import neighborhood_activity_tracker
except ImportError:
    neighborhood_activity_tracker = None

# Import your existing real estate tools (only the ones that exist)
try:
    from tools_agent.utils.tools import (
        # Listing tools
        make_listing,
        insert_listing,
        
        # Market research and valuation tools
        market_trends,
        generate_cma,
        quick_property_valuation,
        
        # Professional finder tools
        find_mortgage_lender,
        find_real_estate_attorney,
        find_title_company,
        find_appraiser,
        find_real_estate_photographer,
        find_home_inspector,
        
        # Marketing and scheduling tools
        schedule_open_house,
        post_to_facebook,
        send_open_house_emails,
        generate_property_listing_tweet,
        post_to_twitter,
    )
except ImportError as e:
    print(f"Warning: Could not import some tools: {e}")
    make_listing = None
    insert_listing = None
    market_trends = None
    generate_cma = None
    quick_property_valuation = None
    find_mortgage_lender = None
    find_real_estate_attorney = None
    find_title_company = None
    find_appraiser = None
    find_real_estate_photographer = None
    find_home_inspector = None
    schedule_open_house = None
    post_to_facebook = None
    send_open_house_emails = None
    generate_property_listing_tweet = None
    post_to_twitter = None

# Import Q&A tools with error handling
try:
    from tools_agent.utils.tools.QnA import (
        query_documents,
        list_available_documents,
        refresh_document_index
    )
except ImportError:
    print("Warning: Q&A tools not available")
    query_documents = None
    list_available_documents = None
    refresh_document_index = None

UNEDITABLE_SYSTEM_PROMPT = "\nIf you need specific property data or market information that you don't have access to, let the user know and guide them on how to find that information through available tools."

DEFAULT_SYSTEM_PROMPT = (
    "You are a knowledgeable and supportive AI real estate agent named Vesty that helps homeowners navigate the For Sale By Owner (FSBO) process. Greet the user and introduce yourself. "
    "You have access to comprehensive tools that let you create property listings, find professional services, generate market analysis, schedule showings, provide pricing guidance, "
    "analyze documents, and answer questions about uploaded files. "
    "When users ask for help, use the appropriate tools and always make sure to inform them of the next steps in their FSBO journey. "
    "You can also help users analyze documents they upload - contracts, inspection reports, market data, or any real estate related documents. "
    "Your goal is to assist sellers in effectively marketing and managing their property sale without needing a traditional agent, while connecting them with the right professionals when needed."
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
                    {"label": "Claude Sonnet 4", "value": "anthropic:claude-sonnet-4-0"},
                    {"label": "Claude 3.7 Sonnet", "value": "anthropic:claude-3-7-sonnet-latest"},
                    {"label": "Claude 3.5 Sonnet", "value": "anthropic:claude-3-5-sonnet-latest"},
                    {"label": "Claude 3.5 Haiku", "value": "anthropic:claude-3-5-haiku-latest"},
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
        default=0.7,
        metadata={
            "x_oap_ui_config": {
                "type": "slider",
                "default": 0.7,
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
    if api_keys and api_keys.get(key_name):
        return api_keys[key_name]
    
    # Fallback to environment variable
    return os.getenv(key_name)

async def graph(config: RunnableConfig):
    cfg = GraphConfigPydantic(**config.get("configurable", {}))
    
    # Complete list of tools
    tools = [
        make_listing,
        insert_listing,
        market_trends,
        generate_cma,
        quick_property_valuation,
        find_mortgage_lender,
        find_real_estate_attorney,
        find_title_company,
        find_appraiser,
        find_real_estate_photographer,
        find_home_inspector,
        schedule_open_house,
        post_to_facebook,
        send_open_house_emails,
        generate_property_listing_tweet,
        post_to_twitter,
        query_documents,
        list_available_documents,
        refresh_document_index
    ]

    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )

    # LangGraph 0.4.x compatible signature
    from langchain_core.messages import SystemMessage
    try:
        return create_react_agent(
            model=model,
            tools=tools,
            messages_modifier=SystemMessage(content=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT)
        )
    except TypeError:
        return create_react_agent(
            model=model,
            tools=tools,
            system_prompt=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT
        )
