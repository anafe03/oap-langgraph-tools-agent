import os
from langchain_core.runnables import RunnableConfig
from typing import Optional, List
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from tools_agent.utils.tools import create_rag_tool
from langchain.chat_models import init_chat_model
from tools_agent.utils.token import fetch_tokens
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from langchain_core.tools import StructuredTool
from tools_agent.utils.tools import (
    wrap_mcp_authenticate_tool,
    create_langchain_mcp_tool,
)

# Import all your existing tools
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

# Import the document Q&A tools (if they exist)
try:
    from tools_agent.utils.tools.QnA import (
        query_documents,
        list_available_documents,
        refresh_document_index
    )
    QNA_TOOLS_AVAILABLE = True
except ImportError:
    QNA_TOOLS_AVAILABLE = False

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
    """The URL of the rag server"""
    collections: Optional[List[str]] = None
    """The collections to use for rag"""

class MCPConfig(BaseModel):
    url: Optional[str] = Field(
        default=None,
        optional=True,
    )
    """The URL of the MCP server"""
    tools: Optional[List[str]] = Field(
        default=None,
        optional=True,
    )
    """The tools to make available to the LLM"""
    auth_required: Optional[bool] = Field(
        default=False,
        optional=True,
    )
    """Whether the MCP server requires authentication"""

class GraphConfigPydantic(BaseModel):
    model_name: Optional[str] = Field(
        default="openai:gpt-4o",
        metadata={
            "x_oap_ui_config": {
                "type": "select",
                "default": "openai:gpt-4o",
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
    mcp_config: Optional[MCPConfig] = Field(
        default=None,
        optional=True,
        metadata={
            "x_oap_ui_config": {
                "type": "mcp",
            }
        },
    )
    rag: Optional[RagConfig] = Field(
        default=None,
        optional=True,
        metadata={
            "x_oap_ui_config": {
                "type": "rag",
            }
        },
    )

def get_api_key_for_model(model_name: str, config: RunnableConfig):
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
    api_keys = config.get("configurable", {}).get("apiKeys", {})
    if api_keys and api_keys.get(key_name) and len(api_keys[key_name]) > 0:
        return api_keys[key_name]
    # Fallback to environment variable
    return os.getenv(key_name)

async def graph(config: RunnableConfig):
    cfg = GraphConfigPydantic(**config.get("configurable", {}))
    
    # Start with your existing real estate tools
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
    ]
    
    # Add Q&A tools if available
    if QNA_TOOLS_AVAILABLE:
        tools.extend([
            query_documents,
            list_available_documents,
            refresh_document_index
        ])

    # RAG tools (optional)
    supabase_token = config.get("configurable", {}).get("x-supabase-access-token")
    if cfg.rag and cfg.rag.rag_url and cfg.rag.collections and supabase_token:
        for collection in cfg.rag.collections:
            rag_tool = await create_rag_tool(
                cfg.rag.rag_url, collection, supabase_token
            )
            tools.append(rag_tool)

    # MCP tools (optional)
    if cfg.mcp_config and cfg.mcp_config.auth_required:
        mcp_tokens = await fetch_tokens(config)
    else:
        mcp_tokens = None
        
    if (
        cfg.mcp_config
        and cfg.mcp_config.url
        and cfg.mcp_config.tools
        and (mcp_tokens or not cfg.mcp_config.auth_required)
    ):
        server_url = cfg.mcp_config.url.rstrip("/") + "/mcp"
        tool_names_to_find = set(cfg.mcp_config.tools)
        fetched_mcp_tools_list: list[StructuredTool] = []
        names_of_tools_added = set()

        headers = (
            mcp_tokens is not None
            and {"Authorization": f"Bearer {mcp_tokens['access_token']}"}
            or None
        )
        
        try:
            async with streamablehttp_client(server_url, headers=headers) as streams:
                read_stream, write_stream, _ = streams
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    page_cursor = None

                    while True:
                        tool_list_page = await session.list_tools(cursor=page_cursor)

                        if not tool_list_page or not tool_list_page.tools:
                            break

                        for mcp_tool in tool_list_page.tools:
                            if not tool_names_to_find or (
                                mcp_tool.name in tool_names_to_find
                                and mcp_tool.name not in names_of_tools_added
                            ):
                                langchain_tool = create_langchain_mcp_tool(
                                    mcp_tool, mcp_server_url=server_url, headers=headers
                                )
                                fetched_mcp_tools_list.append(
                                    wrap_mcp_authenticate_tool(langchain_tool)
                                )
                                if tool_names_to_find:
                                    names_of_tools_added.add(mcp_tool.name)

                        page_cursor = tool_list_page.nextCursor

                        if not page_cursor:
                            break
                        if tool_names_to_find and len(names_of_tools_added) == len(
                            tool_names_to_find
                        ):
                            break

                    tools.extend(fetched_mcp_tools_list)
        except Exception as e:
            print(f"Failed to fetch MCP tools: {e}")
            pass

    # Initialize the model
    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )

    # FIXED: Remove config_schema to avoid input_schema error
    return create_react_agent(
        prompt=cfg.system_prompt + UNEDITABLE_SYSTEM_PROMPT,
        model=model,
        tools=tools,
        # REMOVED: config_schema=GraphConfigPydantic,  # This was causing the input_schema error
    )