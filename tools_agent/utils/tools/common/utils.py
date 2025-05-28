"""
Common utility functions shared across real estate tools.
"""
import re
from typing import Dict, Optional
from datetime import datetime


def extract_price_from_text(text: str) -> str:
    """Extract price information from text snippets."""
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


def calculate_price_per_sqft(price_str: str, sqft: int) -> str:
    """Calculate price per square foot."""
    try:
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


def extract_business_name(title: str, snippet: str) -> str:
    """Extract actual business name from title and snippet."""
    # Clean up title
    title = re.sub(r'^(TOP \d+|Best|Find|Get|Search)\s+', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+(near|in)\s+.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*-\s*.*Yelp.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*-\s*.*Google.*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s*\|\s*.*$', '', title)
    
    # Try to extract business name from snippet if title is generic
    if len(title) < 10 or any(word in title.lower() for word in ["photographer", "attorney", "company"]):
        name_patterns = [
            r'"([^"]+)"',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Photography|Law|Attorney|Company)',
            r'Contact\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+is\s+a'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, snippet)
            if matches:
                return matches[0].strip()
    
    return title.strip() if title.strip() else "Professional Service"


def extract_phone(text: str) -> str:
    """Extract phone number from text."""
    phone_patterns = [
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',
        r'(?:Phone|Call|Tel):?\s*(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            phone = matches[0] if isinstance(matches[0], str) else matches[0]
            return phone.strip()
    return "📞 Call for info"


def extract_address(text: str) -> str:
    """Extract address from text."""
    address_patterns = [
        r'\d+\s+[A-Za-z0-9\s,\.]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)[A-Za-z0-9\s,\.]*, [A-Z]{2}\s*\d{5}',
        r'\d+\s+[A-Za-z\s,\.]+, [A-Za-z\s]+, [A-Z]{2}\s*\d{5}',
        r'(?:Address|Located):?\s*([^\n\r\.]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr)[^\n\r\.]*)'
    ]
    
    for pattern in address_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            address = matches[0].strip()
            return address[:60] + "..." if len(address) > 60 else address
    return "📍 Address on website"


def extract_rating(text: str) -> str:
    """Extract rating from text."""
    rating_patterns = [
        r'(\d+\.?\d*)\s*(?:out of|\/)\s*5\s*stars?',
        r'(\d+\.?\d*)\s*stars?',
        r'Rating:?\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\/5',
        r'Rated\s+(\d+\.?\d*)'
    ]
    
    for pattern in rating_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            rating = float(matches[0])
            stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
            return f"{stars} ({rating}/5)"
    return "⭐ Not rated yet"


def format_professional_card(result: Dict, index: int) -> str:
    """Format each professional as a clean card."""
    card = f"""
┌─ **{index}. {result['name']}**
│
├ 📍 **Address:** {result['address']}
├ 📞 **Phone:** {result['phone']}  
├ ⭐ **Rating:** {result['rating']}
└ 🌐 **Website:** [Click to Visit]({result['url']})

"""
    return card


def validate_date_format(date_str: str) -> Optional[datetime]:
    """Validate and parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def format_currency(amount: str) -> str:
    """Format currency string consistently."""
    # Remove any existing formatting
    clean_amount = re.sub(r'[^\d.]', '', amount)
    try:
        num_amount = float(clean_amount)
        return f"${num_amount:,.0f}"
    except ValueError:
        return amount


def generate_property_summary(bedrooms: int, bathrooms: float, square_feet: int, 
                            property_type: str = "Single Family") -> str:
    """Generate a standardized property summary string."""
    return f"{bedrooms} BR | {bathrooms} BA | {square_feet:,} sq ft {property_type}"