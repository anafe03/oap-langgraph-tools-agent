from typing import Annotated
from langchain_core.tools import StructuredTool, ToolException, tool
import aiohttp
import re
from langchain_core.tools import tool
from typing import Annotated






##TODO

##MARKET Trends tools
#pulls local rent sales data 

##listing tool:
##a tool that list on our website
##and then advises them how to list on zillow?, redfin etc


#generate_CMA:
#instant valuation tool pillls comps  Generate CMA report, visual this is

#generate disclosure:
#  checklist by state

#create social post:
#specifically for the chat history

#schedule open house:
##updates our site, sends emails to prospective buyers, and posts on social media

#buyer inquirer responder:
#  either answer or raises questions
# , you can monitor the conversation and approve or autodefer
#through emails? or even chat or chat then send email?


#coordinate showimgs
#instead of calendar talk to bot conversational
#ive changed my mind about both



# we should have a tool to list on our site
#and a tool for the bot to coordinate showings
#is two way bot interaction a thing?? is that weird
#



#video tour maker
#adds  captions music and call to action


#Social Social Media Scheduler
#Schedules auto-generated posts for Instagram, FB, X, TikTok, LinkedIn about the listing or product.

##AI Lead Qualifier
#Takes inbound email, form, or chat, and extracts intent, budget, and urgency.
#Sends follow-ups or routes to human agent.

##vesty needs access to calendar google calendar 

#@tool(name="syndicate_listing", description="Send a completed FSBO listing to the MLS via API for broader exposure.")



import os
import aiohttp
from typing import Annotated
from langchain_core.tools import ToolException
import os
import aiohttp
from typing import Annotated
from langchain_core.tools import ToolException
from dotenv import load_dotenv

load_dotenv()  # If you're using a .env file

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is not set in the environment variables.")


import os
import aiohttp
from typing import Annotated
from langchain_core.tools import ToolException

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

async def market_trends(
    location: Annotated[str, "The location (city, state, or zip code) to fetch market trends for"]
) -> dict:
    """
    Fetch local market research data using the Tavily search API.
    """
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
                # Optionally, extract only titles/snippets/links for brevity
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



async def syndicate_listing(
    title: Annotated[str, "The listing title"],
    address: Annotated[str, "The property address"],
    price: Annotated[str, "The listing price"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Total square footage"],
    description: Annotated[str, "The detailed listing description"],
    access_token: Annotated[str, "Your API token to authenticate with the MLS service"],
    mls_api_url: Annotated[str, "The URL of the MLS listing API endpoint"]
) -> str:
    """Submits the listing data to the MLS system."""
    payload = {
        "title": title,
        "address": address,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "square_feet": square_feet,
        "description": description
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                mls_api_url,
                json=payload,
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                response.raise_for_status()
                response_data = await response.json()
        return f"✅ Listing successfully syndicated to MLS. MLS ID: {response_data.get('listing_id', 'unknown')}"
    except Exception as e:
        return f"❌ Failed to syndicate listing: {str(e)}"
    
 



#@tool(name="make_listing", description="Create a FSBO property listing by gathering key details from the seller.")
async def make_listing(
    title: Annotated[str, "A short, attention-grabbing title for the property (e.g., 'Charming 3-Bedroom Bungalow with Large Yard')"],
    address: Annotated[str, "The full address of the property"],
    price: Annotated[str, "The asking price for the property (e.g., '$350,000')"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Approximate square footage of the home"],
    description: Annotated[str, "Detailed description of the property, including features, updates, or neighborhood highlights"],
    horse_friendly: Annotated[str, "Do theey allow horses?"]
) -> str:
    """Generate a formatted FSBO property listing based on user inputs."""
    
    listing = f"""
🏡 **{title}**

📍 **Address:** {address}
💰 **Price:** {price}
🛏️ **Bedrooms:** {bedrooms}
🛁 **Bathrooms:** {bathrooms}
📐 **Square Feet:** {square_feet}
horse friednly? 
📝 **Description:**
{description}

_Interested buyers can contact the seller directly to schedule a showing or request more information._
"""
    return listing.strip()



def wrap_mcp_authenticate_tool(tool: StructuredTool) -> StructuredTool:
    """Wrap the tool coroutine to handle `interaction_required` MCP error.

    Tried to obtain the URL from the error, which the LLM can use to render a link."""

    old_coroutine = tool.coroutine

    async def wrapped_mcp_coroutine(**kwargs):
        try:
            response = await old_coroutine(**kwargs)
            return response
        except Exception as e:
            if "TaskGroup" in str(e) and hasattr(e, "__context__"):
                sub_exception = e.__context__
                if hasattr(sub_exception, "error"):
                    e = sub_exception

            if (
                hasattr(e, "error")
                and hasattr(e.error, "code")
                and e.error.code == -32003
                and hasattr(e.error, "data")
            ):
                error_message = (
                    ((e.error.data or {}).get("message") or {}).get("text")
                ) or "Required interaction"

                if url := (e.error.data or {}).get("url"):
                    error_message += f": {url}"

                raise ToolException(error_message)
            raise e

    tool.coroutine = wrapped_mcp_coroutine
    return tool


async def create_rag_tool(rag_url: str, collection_id: str, access_token: str):
    """Create a RAG tool for a specific collection.

    Args:
        rag_url: The base URL for the RAG API server
        collection_id: The ID of the collection to query
        access_token: The access token for authentication

    Returns:
        A structured tool that can be used to query the RAG collection
    """
    if rag_url.endswith("/"):
        rag_url = rag_url[:-1]

    collection_endpoint = f"{rag_url}/collections/{collection_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                collection_endpoint, headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                response.raise_for_status()
                collection_data = await response.json()

        # Get the collection name and sanitize it to match the required regex pattern
        raw_collection_name = collection_data.get("name", f"collection_{collection_id}")

        # Sanitize the name to only include alphanumeric characters, underscores, and hyphens
        # Replace any other characters with underscores
        sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "_", raw_collection_name)

        # Ensure the name is not empty and doesn't exceed 64 characters
        if not sanitized_name:
            sanitized_name = f"collection_{collection_id}"
        collection_name = sanitized_name[:64]

        raw_description = collection_data.get("metadata", {}).get("description")

        if not raw_description:
            collection_description = "Search your collection of documents for results semantically similar to the input query"
        else:
            collection_description = f"Search your collection of documents for results semantically similar to the input query. Collection description: {raw_description}"

        #@tool(name_or_callable=collection_name, description=collection_description)
        async def get_documents(
            query: Annotated[str, "The search query to find relevant documents"],
        ) -> str:
            """Search for documents in the collection based on the query"""

            search_endpoint = f"{rag_url}/collections/{collection_id}/documents/search"
            payload = {"query": query, "limit": 10}

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        search_endpoint,
                        json=payload,
                        headers={"Authorization": f"Bearer {access_token}"},
                    ) as search_response:
                        search_response.raise_for_status()
                        documents = await search_response.json()

                formatted_docs = "<all-documents>\n"

                for doc in documents:
                    doc_id = doc.get("id", "unknown")
                    content = doc.get("page_content", "")
                    formatted_docs += (
                        f'  <document id="{doc_id}">\n    {content}\n  </document>\n'
                    )

                formatted_docs += "</all-documents>"
                return formatted_docs
            except Exception as e:
                return f"<all-documents>\n  <error>{str(e)}</error>\n</all-documents>"

        return get_documents

    except Exception as e:
        raise Exception(f"Failed to create RAG tool: {str(e)}")








import os
import httpx

AZURE_ENDPOINT = os.getenv("AZURE_CV_ENDPOINT")  # e.g. "https://<your-resource-name>.cognitiveservices.azure.com/"
AZURE_KEY = os.getenv("AZURE_CV_KEY")

async def generate_caption_from_image(image_url: str) -> str:
    """Generate a natural language caption for an image using Azure Computer Vision API."""
    endpoint = f"{AZURE_ENDPOINT}/vision/v3.2/describe"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_KEY,
        "Content-Type": "application/json",
    }
    data = {"url": image_url}
    async with httpx.AsyncClient() as client:
        response = await client.post(endpoint, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        result = response.json()
        # The API returns a list of captions, pick the first and its confidence
        caption = result.get("description", {}).get("captions", [{}])[0]
        text = caption.get("text", "")
        confidence = caption.get("confidence", 0)
        return f"Caption: {text} (confidence: {confidence:.2f})" if text else "No caption generated."










import os
import aiohttp
from typing import Annotated, List, Dict
from langchain_core.tools import tool, ToolException

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

async def _search_professionals(
    profession: str, 
    location: str, 
    additional_keywords: str = ""
) -> Dict:
    """
    Generic function to search for real estate professionals using Tavily API.
    """
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    query = f"{profession} {location} {additional_keywords} contact phone website"
    payload = {
        "query": query,
        "max_results": 8,
        "search_depth": "advanced",
        "include_domains": ["zillow.com", "realtor.com", "yelp.com", "google.com", "angieslist.com"]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_message = await response.text()
                    raise ToolException(
                        f"Failed to find {profession} in {location}. "
                        f"API responded with status {response.status}: {error_message}"
                    )
                data = await response.json()
                
                results = []
                for item in data.get("results", []):
                    result = {
                        "name": item.get("title", "").replace(" - ", " | "),
                        "url": item.get("url", ""),
                        "snippet": item.get("snippet", ""),
                        "domain": item.get("url", "").split("//")[-1].split("/")[0] if item.get("url") else ""
                    }
                    results.append(result)
                
                return {
                    "location": location,
                    "profession": profession,
                    "results": results,
                    "total_found": len(results)
                }
    except Exception as e:
        raise ToolException(f"An error occurred searching for {profession}: {str(e)}")

#@tool(name="find_bank", description="Find banks and mortgage lenders in a specific area for real estate financing")
async def find_bank(
    location: Annotated[str, "The location (city, state, or zip code) to search for banks and lenders"]
) -> str:
    """Find local banks and mortgage lenders for real estate financing."""
    try:
        data = await _search_professionals("mortgage lender bank", location, "home loan real estate financing")
        
        result_text = f"🏦 **Banks & Mortgage Lenders in {location}**\n\n"
        
        if data["total_found"] == 0:
            return f"No banks or lenders found in {location}. Try searching in a nearby larger city."
        
        for i, result in enumerate(data["results"][:6], 1):
            result_text += f"**{i}. {result['name']}**\n"
            result_text += f"   🔗 {result['url']}\n"
            if result['snippet']:
                result_text += f"   📝 {result['snippet'][:150]}...\n"
            result_text += "\n"
        
        result_text += f"💡 **Tip:** Contact multiple lenders to compare rates and terms. Consider both local banks and national lenders for the best deal."
        
        return result_text
        
    except Exception as e:
        return f"❌ Error finding banks: {str(e)}"

#@tool(name="find_title_company", description="Find title companies and escrow services in a specific area")
async def find_title_company(
    location: Annotated[str, "The location (city, state, or zip code) to search for title companies"]
) -> str:
    """Find local title companies and escrow services for real estate transactions."""
    try:
        data = await _search_professionals("title company escrow", location, "real estate closing settlement")
        
        result_text = f"📋 **Title Companies & Escrow Services in {location}**\n\n"
        
        if data["total_found"] == 0:
            return f"No title companies found in {location}. Try searching in a nearby larger city."
        
        for i, result in enumerate(data["results"][:6], 1):
            result_text += f"**{i}. {result['name']}**\n"
            result_text += f"   🔗 {result['url']}\n"
            if result['snippet']:
                result_text += f"   📝 {result['snippet'][:150]}...\n"
            result_text += "\n"
        
        result_text += f"💡 **Tip:** Title companies handle title searches, insurance, and closing coordination. Choose one with good reviews and competitive pricing."
        
        return result_text
        
    except Exception as e:
        return f"❌ Error finding title companies: {str(e)}"

#@tool(name="find_real_estate_attorney", description="Find real estate attorneys in a specific area")
async def find_real_estate_attorney(
    location: Annotated[str, "The location (city, state, or zip code) to search for real estate attorneys"]
) -> str:
    """Find local real estate attorneys for legal assistance with property transactions."""
    try:
        data = await _search_professionals("real estate attorney lawyer", location, "property law closing contract review")
        
        result_text = f"⚖️ **Real Estate Attorneys in {location}**\n\n"
        
        if data["total_found"] == 0:
            return f"No real estate attorneys found in {location}. Try searching in a nearby larger city."
        
        for i, result in enumerate(data["results"][:6], 1):
            result_text += f"**{i}. {result['name']}**\n"
            result_text += f"   🔗 {result['url']}\n"
            if result['snippet']:
                result_text += f"   📝 {result['snippet'][:150]}...\n"
            result_text += "\n"
        
        result_text += f"💡 **Tip:** Real estate attorneys can review contracts, handle complex transactions, and resolve legal issues. Some states require attorney involvement in closings."
        
        return result_text
        
    except Exception as e:
        return f"❌ Error finding real estate attorneys: {str(e)}"

#@tool(name="find_real_estate_photographer", description="Find real estate photographers in a specific area")
async def find_real_estate_photographer(
    location: Annotated[str, "The location (city, state, or zip code) to search for real estate photographers"]
) -> str:
    """Find local real estate photographers for property listing photos."""
    try:
        data = await _search_professionals("real estate photographer", location, "property photography listing photos drone aerial")
        
        result_text = f"📸 **Real Estate Photographers in {location}**\n\n"
        
        if data["total_found"] == 0:
            return f"No real estate photographers found in {location}. Try searching in a nearby larger city."
        
        for i, result in enumerate(data["results"][:6], 1):
            result_text += f"**{i}. {result['name']}**\n"
            result_text += f"   🔗 {result['url']}\n"
            if result['snippet']:
                result_text += f"   📝 {result['snippet'][:150]}...\n"
            result_text += "\n"
        
        result_text += f"💡 **Tip:** Quality photos are crucial for selling your home. Look for photographers who offer drone shots, virtual tours, and quick turnaround times."
        
        return result_text
        
    except Exception as e:
        return f"❌ Error finding real estate photographers: {str(e)}"

#@tool(name="find_inspector", description="Find home inspectors in a specific area")
async def find_inspector(
    location: Annotated[str, "The location (city, state, or zip code) to search for home inspectors"]
) -> str:
    """Find local certified home inspectors for property inspections."""
    try:
        data = await _search_professionals("home inspector", location, "certified property inspection structural mechanical electrical")
        
        result_text = f"🔍 **Home Inspectors in {location}**\n\n"
        
        if data["total_found"] == 0:
            return f"No home inspectors found in {location}. Try searching in a nearby larger city."
        
        for i, result in enumerate(data["results"][:6], 1):
            result_text += f"**{i}. {result['name']}**\n"
            result_text += f"   🔗 {result['url']}\n"
            if result['snippet']:
                result_text += f"   📝 {result['snippet'][:150]}...\n"
            result_text += "\n"
        
        result_text += f"💡 **Tip:** Choose an inspector certified by ASHI, InterNACHI, or your state's licensing board. Get the inspection done within your due diligence period."
        
        return result_text
        
    except Exception as e:
        return f"❌ Error finding home inspectors: {str(e)}"

#@tool(name="find_appraiser", description="Find certified real estate appraisers in a specific area")
async def find_appraiser(
    location: Annotated[str, "The location (city, state, or zip code) to search for real estate appraisers"]
) -> str:
    """Find local certified real estate appraisers for property valuations."""
    try:
        data = await _search_professionals("real estate appraiser", location, "certified property valuation appraisal")
        
        result_text = f"📊 **Real Estate Appraisers in {location}**\n\n"
        
        if data["total_found"] == 0:
            return f"No real estate appraisers found in {location}. Try searching in a nearby larger city."
        
        for i, result in enumerate(data["results"][:6], 1):
            result_text += f"**{i}. {result['name']}**\n"
            result_text += f"   🔗 {result['url']}\n"
            if result['snippet']:
                result_text += f"   📝 {result['snippet'][:150]}...\n"
            result_text += "\n"
        
        result_text += f"💡 **Tip:** Appraisers must be licensed or certified in your state. Banks typically order appraisals for mortgages, but you can get independent appraisals for pricing guidance."
        
        return result_text
        
    except Exception as e:
        return f"❌ Error finding real estate appraisers: {str(e)}"

# Bonus tool: Find all professionals at once
#@tool(name="find_all_real_estate_professionals", description="Find all types of real estate professionals in one search")
async def find_all_real_estate_professionals(
    location: Annotated[str, "The location (city, state, or zip code) to search for all real estate professionals"]
) -> str:
    """Find all types of real estate professionals in your area - a comprehensive search."""
    try:
        result_text = f"🏠 **Complete Real Estate Professional Directory for {location}**\n\n"
        
        # Search for each profession type
        professions = [
            ("🏦 Banks & Lenders", "mortgage lender bank", "home loan financing"),
            ("📋 Title Companies", "title company escrow", "closing settlement"),
            ("⚖️ Real Estate Attorneys", "real estate attorney", "property law"),
            ("📸 Photographers", "real estate photographer", "property photos"),
            ("🔍 Home Inspectors", "home inspector", "property inspection"),
            ("📊 Appraisers", "real estate appraiser", "property valuation")
        ]
        
        for section_title, profession, keywords in professions:
            try:
                data = await _search_professionals(profession, location, keywords)
                result_text += f"## {section_title}\n"
                
                if data["total_found"] > 0:
                    for i, result in enumerate(data["results"][:3], 1):  # Top 3 for each category
                        result_text += f"{i}. **{result['name']}** - {result['url']}\n"
                else:
                    result_text += "No results found for this category.\n"
                result_text += "\n"
                
            except Exception as e:
                result_text += f"## {section_title}\n"
                result_text += f"Error searching this category: {str(e)}\n\n"
        
        result_text += "💡 **Pro Tip:** Save this list and contact multiple professionals in each category to compare services and pricing!"
        
        return result_text
        
    except Exception as e:
        return f"❌ Error in comprehensive search: {str(e)}"
    





######CMA TOOOL GET THIS IN A SEPERATE FILE

import os
import aiohttp
import asyncio
from typing import Annotated, Dict, List
from langchain_core.tools import tool, ToolException
from datetime import datetime, timedelta
import json

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

async def _search_property_data(query: str, max_results: int = 10) -> Dict:
    """Search for property data using Tavily API with real estate focus."""
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

def _extract_price_from_text(text: str) -> str:
    """Extract price information from text snippets."""
    import re
    # Look for price patterns like $XXX,XXX or $X.XM
    price_patterns = [
        r'\$[\d,]+(?:\.\d+)?[KkMm]?',
        r'[\d,]+(?:\.\d+)?[KkMm]?\s*(?:thousand|million|k|m)',
        r'Listed\s+at\s+\$[\d,]+',
        r'Sold\s+for\s+\$[\d,]+',
        r'Price:\s*\$[\d,]+'
    ]
    
    for pattern in price_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]
    return "Price not found"

def _calculate_price_per_sqft(price_str: str, sqft: int) -> str:
    """Calculate price per square foot."""
    try:
        # Extract numeric value from price string
        import re
        price_match = re.search(r'([\d,]+)', price_str.replace('$', '').replace(',', ''))
        if price_match and sqft > 0:
            price = int(price_match.group(1))
            if 'k' in price_str.lower() or 'thousand' in price_str.lower():
                price *= 1000
            elif 'm' in price_str.lower() or 'million' in price_str.lower():
                price *= 1000000
            
            price_per_sqft = price / sqft
            return f"${price_per_sqft:.0f}/sqft"
    except:
        pass
    return "N/A"

#@tool(name="generate_cma", description="Generate a comprehensive Comparative Market Analysis (CMA) report for a property")
async def generate_cma(
    address: Annotated[str, "The subject property address"],
    bedrooms: Annotated[int, "Number of bedrooms in the subject property"],
    bathrooms: Annotated[float, "Number of bathrooms in the subject property"],
    square_feet: Annotated[int, "Square footage of the subject property"],
    property_type: Annotated[str, "Type of property (e.g., Single Family, Condo, Townhouse)"] = "Single Family",
    radius_miles: Annotated[float, "Search radius in miles for comparable properties"] = 1.0
) -> str:
    """Generate a comprehensive CMA report with comparable sales, market trends, and pricing analysis."""
    
    try:
        # Extract location from address for searches
        location_parts = address.split(',')
        if len(location_parts) >= 2:
            city_state = ','.join(location_parts[-2:]).strip()
        else:
            city_state = address
        
        # Create search queries for different data types
        search_queries = [
            f"recently sold homes {city_state} {bedrooms} bedroom {bathrooms} bathroom {property_type}",
            f"home sales {city_state} {square_feet} square feet comparable properties",
            f"real estate market trends {city_state} 2024 home prices",
            f"active listings {city_state} {bedrooms}br {bathrooms}ba for sale"
        ]
        
        # Execute searches concurrently
        search_results = await asyncio.gather(
            *[_search_property_data(query, 8) for query in search_queries],
            return_exceptions=True
        )
        
        # Process results
        sold_properties = []
        active_listings = []
        market_trends = []
        
        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                continue
                
            for item in result.get("results", []):
                property_data = {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", ""),
                    "price": _extract_price_from_text(item.get("snippet", "")),
                    "source": item.get("url", "").split("//")[-1].split("/")[0]
                }
                
                # Categorize based on search query
                if i == 0 and ("sold" in item.get("snippet", "").lower() or "sale" in item.get("title", "").lower()):
                    sold_properties.append(property_data)
                elif i == 3 and ("for sale" in item.get("snippet", "").lower() or "listing" in item.get("snippet", "").lower()):
                    active_listings.append(property_data)
                elif i == 2:
                    market_trends.append(property_data)
        
        # Generate the CMA report
        current_date = datetime.now().strftime("%B %d, %Y")
        
        cma_report = f"""
# 🏠 COMPARATIVE MARKET ANALYSIS (CMA)

**Property Address:** {address}  
**Report Date:** {current_date}  
**Property Type:** {property_type}  
**Bedrooms:** {bedrooms} | **Bathrooms:** {bathrooms} | **Square Feet:** {square_feet:,}

---

## 📊 EXECUTIVE SUMMARY

This Comparative Market Analysis provides a comprehensive evaluation of the subject property's market value based on recent comparable sales, current market conditions, and active competition in the area.

**Search Parameters:**
- Property Type: {property_type}
- Bedrooms: {bedrooms}
- Bathrooms: {bathrooms}
- Square Footage: {square_feet:,}
- Search Radius: {radius_miles} miles

---

## 🏘️ RECENTLY SOLD COMPARABLES

"""
        
        if sold_properties:
            cma_report += "The following properties have sold recently in your area:\n\n"
            for i, prop in enumerate(sold_properties[:6], 1):
                price_per_sqft = _calculate_price_per_sqft(prop["price"], square_feet)
                cma_report += f"**{i}. {prop['title']}**\n"
                cma_report += f"   💰 **Price:** {prop['price']}\n"
                cma_report += f"   📐 **Price/SqFt:** {price_per_sqft}\n"
                cma_report += f"   🔗 **Source:** {prop['source']}\n"
                cma_report += f"   📝 **Details:** {prop['snippet'][:200]}...\n"
                cma_report += f"   🌐 **Link:** {prop['url']}\n\n"
        else:
            cma_report += "No recent comparable sales found in the immediate area. Consider expanding the search radius.\n\n"
        
        cma_report += "---\n\n## 🏪 ACTIVE COMPETITION\n\n"
        
        if active_listings:
            cma_report += "Current properties for sale in your area:\n\n"
            for i, prop in enumerate(active_listings[:6], 1):
                price_per_sqft = _calculate_price_per_sqft(prop["price"], square_feet)
                cma_report += f"**{i}. {prop['title']}**\n"
                cma_report += f"   💰 **Asking Price:** {prop['price']}\n"
                cma_report += f"   📐 **Price/SqFt:** {price_per_sqft}\n"
                cma_report += f"   🔗 **Source:** {prop['source']}\n"
                cma_report += f"   📝 **Details:** {prop['snippet'][:200]}...\n"
                cma_report += f"   🌐 **Link:** {prop['url']}\n\n"
        else:
            cma_report += "Limited active listings found in the immediate area.\n\n"
        
        cma_report += "---\n\n## 📈 MARKET TRENDS\n\n"
        
        if market_trends:
            cma_report += "Current market conditions and trends:\n\n"
            for i, trend in enumerate(market_trends[:4], 1):
                cma_report += f"**{i}. {trend['title']}**\n"
                cma_report += f"   📊 **Insight:** {trend['snippet'][:250]}...\n"
                cma_report += f"   🔗 **Source:** {trend['source']}\n"
                cma_report += f"   🌐 **Link:** {trend['url']}\n\n"
        else:
            cma_report += "Market trend data not available for this specific area.\n\n"
        
        # Add pricing recommendations
        cma_report += """---

## 💡 PRICING RECOMMENDATIONS

Based on the comparative analysis above, consider the following pricing strategies:

### 📋 **Pricing Strategy Options:**

1. **🎯 Competitive Pricing:** Price at or slightly below comparable sold properties to attract quick offers
2. **📈 Market Rate Pricing:** Price in line with current market averages for similar properties
3. **💰 Premium Pricing:** Price above market if your property has unique features or superior condition

### 🔍 **Key Considerations:**
- **Days on Market:** How long similar properties are taking to sell
- **Price Reductions:** Whether comparable properties had to reduce their asking prices
- **Market Conditions:** Current buyer demand and inventory levels
- **Property Condition:** Your home's condition relative to the comparables
- **Unique Features:** Special amenities or upgrades that add value

---

## ⚠️ IMPORTANT DISCLAIMERS

- This CMA is for informational purposes and should not replace a professional appraisal
- Property values can fluctuate based on market conditions, property condition, and other factors
- Consult with a licensed real estate professional for official valuation guidance
- Data accuracy depends on available public information and listing sources

---

## 📞 NEXT STEPS

1. **Review Comparables:** Visit or drive by comparable properties when possible
2. **Professional Consultation:** Consider hiring a licensed appraiser for official valuation
3. **Market Timing:** Monitor market conditions and adjust pricing strategy accordingly
4. **Property Preparation:** Ensure your home is in optimal condition for sale

*Report generated on {current_date}*
"""
        
        return cma_report.strip()
        
    except Exception as e:
        return f"❌ Error generating CMA report: {str(e)}"

# Bonus tool for quick property valuation
#@tool(name="quick_property_valuation", description="Get a quick property value estimate based on comparable sales")
async def quick_property_valuation(
    address: Annotated[str, "The property address to value"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Square footage of the property"]
) -> str:
    """Get a quick property valuation based on recent sales data."""
    
    try:
        # Extract location for search
        location_parts = address.split(',')
        if len(location_parts) >= 2:
            city_state = ','.join(location_parts[-2:]).strip()
        else:
            city_state = address
        
        # Search for recent sales
        query = f"recently sold homes {city_state} {bedrooms} bedroom {bathrooms} bathroom {square_feet} square feet"
        search_result = await _search_property_data(query, 5)
        
        valuation_text = f"🏠 **Quick Valuation for {address}**\n\n"
        valuation_text += f"**Property Details:** {bedrooms}BR | {bathrooms}BA | {square_feet:,} sq ft\n\n"
        
        if search_result.get("results"):
            valuation_text += "**📊 Based on Recent Comparable Sales:**\n\n"
            
            total_estimated_value = 0
            valid_comps = 0
            
            for i, result in enumerate(search_result["results"][:5], 1):
                price = _extract_price_from_text(result.get("snippet", ""))
                price_per_sqft = _calculate_price_per_sqft(price, square_feet)
                
                valuation_text += f"{i}. **{result.get('title', 'Property')}**\n"
                valuation_text += f"   💰 {price} | {price_per_sqft}\n"
                valuation_text += f"   📝 {result.get('snippet', '')[:150]}...\n\n"
            
            valuation_text += f"**💡 Estimated Value Range:** Based on comparable sales, your property may be valued between the range of prices shown above.\n\n"
            valuation_text += f"**⚠️ Note:** This is a preliminary estimate. For accurate valuation, order a professional appraisal or detailed CMA report."
        
        else:
            valuation_text += "❌ No recent comparable sales found. Try expanding your search area or use the full CMA tool for more comprehensive analysis."
        
        return valuation_text
        
    except Exception as e:
        return f"❌ Error generating property valuation: {str(e)}"
    









import os
import aiohttp
import asyncio
from typing import Annotated, Optional, List
from langchain_core.tools import tool, ToolException
from datetime import datetime, timedelta
import json
from urllib.parse import quote

# Email service configuration (you'll need to set these environment variables)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Facebook API configuration (optional)
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")

#@tool(name="schedule_open_house", description="Schedule an open house event with options for email notifications, social media posting, and calendar integration")
async def schedule_open_house(
    property_address: Annotated[str, "The full address of the property for the open house"],
    date: Annotated[str, "Date of the open house (format: YYYY-MM-DD)"],
    start_time: Annotated[str, "Start time of the open house (format: HH:MM AM/PM)"],
    end_time: Annotated[str, "End time of the open house (format: HH:MM AM/PM)"],
    agent_name: Annotated[str, "Name of the listing agent"],
    agent_phone: Annotated[str, "Agent's phone number"],
    agent_email: Annotated[str, "Agent's email address"],
    property_price: Annotated[str, "Asking price of the property (e.g., '$450,000')"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Square footage of the property"],
    special_features: Annotated[str, "Special features or highlights of the property"] = "",
    parking_info: Annotated[str, "Parking information for visitors"] = "Street parking available",
    additional_notes: Annotated[str, "Any additional notes or instructions"] = "",
    send_to_prospects: Annotated[bool, "Whether to send email notifications to prospective buyers"] = True,
    post_to_facebook: Annotated[bool, "Whether to create a Facebook post"] = False,
    add_to_calendar: Annotated[bool, "Whether to generate Google Calendar integration"] = True,
    prospect_emails: Annotated[Optional[List[str]], "List of prospective buyer email addresses"] = None
) -> str:
    """
    Schedule an open house with comprehensive marketing and organization features.
    
    This tool creates:
    - Professional open house announcement
    - Email notifications to prospects
    - Social media post content
    - Google Calendar integration
    - Marketing materials
    """
    
    try:
        # Validate date format
        try:
            event_date = datetime.strptime(date, "%Y-%m-%d")
            formatted_date = event_date.strftime("%A, %B %d, %Y")
        except ValueError:
            return "❌ Invalid date format. Please use YYYY-MM-DD format."
        
        # Create the open house announcement
        announcement = f"""
🏠 **OPEN HOUSE SCHEDULED**

**📍 Property:** {property_address}
**📅 Date:** {formatted_date}
**🕐 Time:** {start_time} - {end_time}
**💰 Price:** {property_price}
**🏡 Details:** {bedrooms} BR | {bathrooms} BA | {square_feet:,} sq ft

**👤 Hosted by:** {agent_name}
**📞 Contact:** {agent_phone}
**📧 Email:** {agent_email}

**✨ Special Features:**
{special_features if special_features else "Beautiful property with many attractive features"}

**🚗 Parking:** {parking_info}

{f"**📝 Additional Information:** {additional_notes}" if additional_notes else ""}

We look forward to seeing you there! Please feel free to reach out with any questions.
"""
        
        result_summary = [announcement]
        result_summary.append("\n" + "="*50 + "\n")
        
        # Generate email content for prospects
        if send_to_prospects:
            email_subject = f"Open House: {property_address} - {formatted_date}"
            email_body = f"""
Dear Prospective Buyer,

You're invited to an exclusive open house viewing!

🏠 PROPERTY DETAILS:
Address: {property_address}
Price: {property_price}
Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Square Feet: {square_feet:,}

📅 OPEN HOUSE DETAILS:
Date: {formatted_date}
Time: {start_time} - {end_time}
Parking: {parking_info}

✨ HIGHLIGHTS:
{special_features if special_features else "This beautiful property offers many attractive features and is located in a desirable area."}

{f"IMPORTANT NOTES: {additional_notes}" if additional_notes else ""}

Please mark your calendar and join us for this exciting opportunity to view this exceptional property. No appointment necessary during open house hours.

For private showings or questions, please contact:
{agent_name}
📞 {agent_phone}
📧 {agent_email}

Best regards,
{agent_name}
Real Estate Professional

---
This email was sent because you expressed interest in properties in this area. If you no longer wish to receive these updates, please reply with "UNSUBSCRIBE".
"""
            
            result_summary.append("📧 **EMAIL NOTIFICATION READY**")
            result_summary.append(f"**Subject:** {email_subject}")
            result_summary.append("**Email Body Created:** ✅")
            
            if prospect_emails and len(prospect_emails) > 0:
                result_summary.append(f"**Recipients:** {len(prospect_emails)} prospects")
                result_summary.append("**Email Status:** Ready to send (requires SMTP configuration)")
            else:
                result_summary.append("**Recipients:** No prospect emails provided")
                result_summary.append("**Action Required:** Provide prospect email addresses to send notifications")
            
            result_summary.append(f"\n**Email Preview:**\n{email_body[:300]}...\n")
        
        # Generate Facebook post content
        if post_to_facebook:
            facebook_post = f"""🏠 OPEN HOUSE ALERT! 🏠

📍 {property_address}
📅 {formatted_date}
🕐 {start_time} - {end_time}
💰 {property_price}

🏡 {bedrooms} bedrooms | {bathrooms} bathrooms | {square_feet:,} sq ft

✨ {special_features if special_features else "Beautiful property with amazing features!"}

🚗 {parking_info}

Hosted by {agent_name} 📞 {agent_phone}

Don't miss this opportunity! See you there! 

#OpenHouse #RealEstate #ForSale #DreamHome #PropertyTour
{f"#{property_address.split(',')[-1].strip().replace(' ', '')}" if ',' in property_address else ""}
"""
            
            result_summary.append("\n📱 **FACEBOOK POST READY**")
            result_summary.append("**Post Content Created:** ✅")
            
            if FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID:
                result_summary.append("**Facebook API:** Configured ✅")
                result_summary.append("**Status:** Ready to post automatically")
            else:
                result_summary.append("**Facebook API:** Not configured")
                result_summary.append("**Action Required:** Set FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID environment variables")
            
            result_summary.append(f"\n**Facebook Post Preview:**\n{facebook_post}\n")
        
        # Generate Google Calendar integration
        if add_to_calendar:
            # Create Google Calendar URL for easy adding
            calendar_title = quote(f"Open House: {property_address}")
            calendar_details = quote(f"Open House at {property_address}\n\nProperty Details:\n- Price: {property_price}\n- {bedrooms} BR, {bathrooms} BA, {square_feet:,} sq ft\n\nHost: {agent_name}\nPhone: {agent_phone}\nEmail: {agent_email}\n\nFeatures: {special_features}\nParking: {parking_info}")
            calendar_location = quote(property_address)
            
            # Convert time to 24-hour format for URL (simplified)
            try:
                start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %I:%M %p")
                end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %I:%M %p")
                
                start_formatted = start_datetime.strftime("%Y%m%dT%H%M%S")
                end_formatted = end_datetime.strftime("%Y%m%dT%H%M%S")
                
                google_calendar_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={calendar_title}&dates={start_formatted}/{end_formatted}&details={calendar_details}&location={calendar_location}"
                
                result_summary.append("\n📅 **GOOGLE CALENDAR INTEGRATION**")
                result_summary.append("**Calendar Event:** Ready ✅")
                result_summary.append(f"**Quick Add URL:** {google_calendar_url[:100]}...")
                result_summary.append("**Action:** Click the URL above to add to your Google Calendar")
                
            except ValueError:
                result_summary.append("\n📅 **GOOGLE CALENDAR INTEGRATION**")
                result_summary.append("**Status:** Error parsing time format")
                result_summary.append("**Action Required:** Verify time format (HH:MM AM/PM)")
        
        # Generate summary and next steps
        result_summary.append("\n" + "="*50)
        result_summary.append("\n🎯 **NEXT STEPS:**")
        
        if send_to_prospects and prospect_emails:
            result_summary.append("1. ✅ Send email notifications to prospects")
        elif send_to_prospects:
            result_summary.append("1. 📝 Collect prospect email addresses and send notifications")
        
        if post_to_facebook:
            if FACEBOOK_PAGE_ACCESS_TOKEN:
                result_summary.append("2. ✅ Post to Facebook page")
            else:
                result_summary.append("2. 📱 Manually post to Facebook using the content above")
        
        if add_to_calendar:
            result_summary.append("3. 📅 Add event to your Google Calendar using the provided link")
        
        result_summary.append("4. 📋 Save this information for your records")
        result_summary.append("5. 🏠 Prepare the property for the open house")
        result_summary.append("6. 📧 Send reminder emails 1-2 days before the event")
        
        # Additional marketing suggestions
        result_summary.append("\n💡 **ADDITIONAL MARKETING IDEAS:**")
        result_summary.append("- Post on Instagram Stories with property photos")
        result_summary.append("- Add open house signs and directional signs")
        result_summary.append("- Update MLS listing with open house information")
        result_summary.append("- Notify neighbors about the open house")
        result_summary.append("- Prepare refreshments and informational materials")
        
        return "\n".join(result_summary)
        
    except Exception as e:
        return f"❌ Error scheduling open house: {str(e)}"

# Helper tool for sending actual emails (requires additional setup)
#@tool(name="send_open_house_emails", description="Send open house email notifications to a list of prospects")
async def send_open_house_emails(
    subject: Annotated[str, "Email subject line"],
    body: Annotated[str, "Email body content"],
    recipient_emails: Annotated[List[str], "List of recipient email addresses"],
    sender_name: Annotated[str, "Name of the sender (agent)"],
    sender_email: Annotated[str, "Sender's email address"]
) -> str:
    """
    Send open house email notifications to prospective buyers.
    Requires SMTP configuration in environment variables.
    """
    
    if not EMAIL_USER or not EMAIL_PASSWORD:
        return """
❌ **Email Configuration Required**

To send emails automatically, please set these environment variables:
- EMAIL_USER: Your email address
- EMAIL_PASSWORD: Your email app password
- SMTP_SERVER: Your SMTP server (default: smtp.gmail.com)
- SMTP_PORT: Your SMTP port (default: 587)

**Alternative:** Copy the email content and send manually through your email client.
"""
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        sent_count = 0
        failed_count = 0
        
        # Create SMTP session
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        for recipient in recipient_emails:
            try:
                # Create message
                msg = MIMEMultipart()
                msg['From'] = f"{sender_name} <{EMAIL_USER}>"
                msg['To'] = recipient
                msg['Subject'] = subject
                
                # Add body
                msg.attach(MIMEText(body, 'plain'))
                
                # Send email
                server.send_message(msg)
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {recipient}: {str(e)}")
        
        server.quit()
        
        return f"""
✅ **Email Sending Complete**

📧 **Results:**
- Successfully sent: {sent_count} emails
- Failed to send: {failed_count} emails
- Total recipients: {len(recipient_emails)}

The open house notifications have been delivered to your prospects!
"""
        
    except Exception as e:
        return f"❌ Error sending emails: {str(e)}"

# Helper tool for Facebook posting (requires Facebook API setup)
#@tool(name="post_to_facebook", description="Post open house announcement to Facebook page")
async def post_to_facebook(
    post_content: Annotated[str, "The content to post on Facebook"],
    page_id: Annotated[str, "Facebook page ID"] = None,
    access_token: Annotated[str, "Facebook page access token"] = None
) -> str:
    """
    Post open house announcement to Facebook page.
    Requires Facebook API configuration.
    """
    
    # Use environment variables if not provided
    if not page_id:
        page_id = FACEBOOK_PAGE_ID
    if not access_token:
        access_token = FACEBOOK_PAGE_ACCESS_TOKEN
    
    if not page_id or not access_token:
        return """
❌ **Facebook API Configuration Required**

To post automatically to Facebook, please set these environment variables:
- FACEBOOK_PAGE_ID: Your Facebook page ID
- FACEBOOK_PAGE_ACCESS_TOKEN: Your page access token

**Alternative:** Copy the post content and share manually on your Facebook page.

**Getting Facebook API Access:**
1. Go to Facebook Developers (developers.facebook.com)
2. Create an app and get page access token
3. Set the environment variables above
"""
    
    try:
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        payload = {
            "message": post_content,
            "access_token": access_token
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    post_id = result.get("id", "unknown")
                    return f"""
✅ **Facebook Post Successful**

🎉 Your open house announcement has been posted to Facebook!
📱 Post ID: {post_id}

The post is now live and visible to your page followers.
"""
                else:
                    error_text = await response.text()
                    return f"❌ Facebook posting failed: {error_text}"
                    
    except Exception as e:
        return f"❌ Error posting to Facebook: {str(e)}"
    


    ###

##tweet stuff

from langchain_core.tools import tool
from typing import Annotated

#@tool(name="generate_property_listing_tweet", description="Generate a short tweet for a property listing.")
def generate_property_listing_tweet(
    title: Annotated[str, "Listing title (e.g., 'Charming 3BR Bungalow')"],
    address: Annotated[str, "Street address (e.g., '1234 Elm St, Chicago, IL')"],
    price: Annotated[str, "Price (e.g., '$420,000')"],
    bedrooms: Annotated[int, "Number of bedrooms"],
    bathrooms: Annotated[float, "Number of bathrooms"],
    square_feet: Annotated[int, "Total square footage"],
) -> str:
    """
    Returns a short tweet string announcing a new property listing.
    """
    tweet = f"""
🏡 {title}
📍 {address}
💰 {price}
🛏️ {bedrooms} bd | 🛁 {bathrooms} ba | 📐 {square_feet} sqft

New on the market!
#realestate #FSBO #homeforsale
""".strip()

    if len(tweet) > 280:
        tweet = tweet[:276] + "..."

    return tweet


import os
import aiohttp
from langchain_core.tools import tool
from typing import Annotated

#@tool(name="post_to_twitter", description="Post any custom message to Twitter.")
async def post_to_twitter(
    text: Annotated[str, "The tweet content (must be under 280 characters)"]
) -> str:
    """
    Posts a plain text tweet to Twitter using the API v2.
    Requires TWITTER_BEARER_TOKEN in .env.
    """
    twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
    tweet_url = "https://api.twitter.com/2/tweets"

    headers = {
        "Authorization": f"Bearer {twitter_token}",
        "Content-Type": "application/json"
    }

    if len(text) > 280:
        return "❌ Tweet exceeds 280 characters."

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                tweet_url,
                json={"text": text},
                headers=headers
            ) as response:
                result = await response.json()
                if response.status == 201 and "data" in result:
                    return f"✅ Tweet posted. Tweet ID: {result['data']['id']}"
                else:
                    return f"❌ Failed to post tweet: {result}"
    except Exception as e:
        return f"❌ Error posting to Twitter: {str(e)}"





#####

