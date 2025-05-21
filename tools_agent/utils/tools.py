from typing import Annotated
from langchain_core.tools import StructuredTool, ToolException, tool
import aiohttp
import re
from langchain_core.tools import tool
from typing import Annotated


#@tool(name="syndicate_listing", description="Send a completed FSBO listing to the MLS via API for broader exposure.")
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

        @tool(name_or_callable=collection_name, description=collection_description)
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



