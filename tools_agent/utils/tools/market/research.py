"""
Market research and trends analysis tools.
"""
import aiohttp
from typing import Annotated
from langchain_core.tools import tool, ToolException
from ..common.config import TAVILY_API_KEY, validate_tavily_api


#@tool(name="market_trends", description="Fetch local market research data for a specific location")
async def market_trends(
    location: Annotated[str, "The location (city, state, or zip code) to fetch market trends for"]
) -> dict:
    """
    Fetch local market research data using the Tavily search API.
    """
    validate_tavily_api()
    
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": f"real estate market trends {location} 2024",
        "max_results": 5,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise ToolException(
                        f"Failed to fetch market trends for {location}. "
                        f"API responded with status {response.status}: {error_message}"
                    )
                data = await response.json()
                # Extract only titles/snippets/links for brevity
                results = [
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                    }
                    for item in data.get("results", [])
                ]
                summary = data.get("summary", "")
                return {
                    "location": location,
                    "summary": summary,
                    "top_results": results,
                }
    except Exception as e:
        raise ToolException(f"An error occurred fetching market trends: {str(e)}")


async def _search_property_data(query: str, max_results: int = 10) -> dict:
    """Search for property data using Tavily API with real estate focus."""
    validate_tavily_api()
    
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_domains": ["zillow.com", "realtor.com", "redfin.com", "homes.com", "trulia.com", "movoto.com"]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise ToolException(f"Search failed with status {response.status}: {error_message}")
                
                return await response.json()
    except Exception as e:
        raise ToolException(f"Error searching property data: {str(e)}")