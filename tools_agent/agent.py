# tools_agent/agent.py - Fixed version with Q&A tools

from langchain_core.runnables import RunnableConfig
from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from tools_agent.utils.tools import create_rag_tool
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from tools_agent.utils.token import fetch_tokens
from tools_agent.utils.tools import wrap_mcp_authenticate_tool

# Import market tools
from tools_agent.utils.tools.market import (neighborhood_activity_tracker)

# Import all existing tools
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
    
    # Integration tools
    create_rag_tool,
    wrap_mcp_authenticate_tool,
)

# Import the new document Q&A tools
from tools_agent.utils.tools.QnA import (
    query_documents,
    list_available_documents,
    refresh_document_index
)

UNEDITABLE_SYSTEM_PROMPT = "\nIf the tool throws an error requiring authentication, provide the user with a Markdown link to the authentication page and prompt them to authenticate."

DEFAULT_SYSTEM_PROMPT = (
    "You are a knowledgeable and supportive AI real estate agent named Vesty that helps homeowners navigate the For Sale By Owner (FSBO) process. Greet the user and introduce yourself. "
    "You have access to comprehensive tools that let you create property listings, find professional services, generate market analysis, schedule showings, provide pricing guidance, "
    "analyze documents, and answer questions about uploaded files. "
    "When users ask for help, use the appropriate tools and always make sure to inform them of the next steps in their FSBO journey. "
    "You can also help users analyze documents they upload - contracts, inspection reports, market data, or any real estate related documents. "
    "Your goal is to assist sellers in effectively marketing and managing their property sale without needing a traditional agent, while connecting them with the right professionals when needed."
)

class RagConfig(BaseModel):
    rag_url: Optional[str] = None
    collections: Optional[List[str]] = None

class MCPConfig(BaseModel):
    url: Optional[str] = Field(default=None, optional=True)
    tools: Optional[List[str]] = Field(default=None, optional=True)

class GraphConfigPydantic(BaseModel):
    model_name: Optional[str] = Field(
        default="openai:gpt-4o",
        metadata={
            "x_oap_ui_config": {
                "type": "select",
                "default": "openai:gpt-4o",
                "description": "The model to use in all generations",
                "options": [
                    {"label": "Claude 3.7 Sonnet", "value": "anthropic:claude-3-7-sonnet-latest"},
                    {"label": "Claude 3.5 Sonnet", "value": "anthropic:claude-3-5-sonnet-latest"},
                    {"label": "GPT 4o", "value": "openai:gpt-4o"},
                    {"label": "GPT 4o mini", "value": "openai:gpt-4o-mini"},
                    {"label": "GPT 4.1", "value": "openai:gpt-4.1"},
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
    mcp_config: Optional[MCPConfig] = Field(default=None, optional=True)
    rag: Optional[RagConfig] = Field(default=None, optional=True)

async def graph(config: RunnableConfig):
    cfg = GraphConfigPydantic(**config.get("configurable", {}))
    
    # Complete list of tools including new Q&A tools
    tools = [
        # Core listing and market tools
        make_listing,
        insert_listing,
        market_trends,
        
        # Valuation and analysis tools
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
        
        # NEW: Document Q&A tools
        query_documents,
        list_available_documents,
        refresh_document_index
    ]

    # RAG tools (optional)
    supabase_token = config.get("configurable", {}).get("x-supabase-access-token")
    if cfg.rag and cfg.rag.rag_url and cfg.rag.collections and supabase_token:
        for collection in cfg.rag.collections:
            rag_tool = await create_rag_tool(cfg.rag.rag_url, collection, supabase_token)
            tools.append(rag_tool)

    # MCP tools (optional)
    if cfg.mcp_config and cfg.mcp_config.url and cfg.mcp_config.tools and (mcp_tokens := await fetch_tokens(config)):
        mcp_client = MultiServerMCPClient(
            connections={
                "mcp_server": {
                    "transport": "streamable_http",
                    "url": cfg.mcp_config.url.rstrip("/") + "/mcp",
                    "headers": {"Authorization": f"Bearer {mcp_tokens['access_token']}"},
                }
            }
        )
        tools.extend([
            wrap_mcp_authenticate_tool(tool)
            for tool in await mcp_client.get_tools()
            if tool.name in cfg.mcp_config.tools
        ])

    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
    )

    return create_react_agent(
        prompt=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT,
        model=model,
        tools=tools,
        config_schema=GraphConfigPydantic,
    )