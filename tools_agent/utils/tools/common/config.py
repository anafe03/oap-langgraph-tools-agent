"""
Common configuration and environment variables for real estate tools.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and Configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_CV_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_CV_KEY")

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Social Media API Configuration
FACEBOOK_PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# Validation functions
def validate_tavily_api():
    """Ensure Tavily API key is configured."""
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY is not set in environment variables.")
    return True

def validate_azure_config():
    """Ensure Azure Computer Vision is configured."""
    if not AZURE_ENDPOINT or not AZURE_KEY:
        raise ValueError("Azure Computer Vision credentials not configured.")
    return True

def validate_email_config():
    """Check if email configuration is available."""
    return bool(EMAIL_USER and EMAIL_PASSWORD)

def validate_facebook_config():
    """Check if Facebook API is configured."""
    return bool(FACEBOOK_PAGE_ACCESS_TOKEN and FACEBOOK_PAGE_ID)

def validate_twitter_config():
    """Check if Twitter API is configured."""
    return bool(TWITTER_BEARER_TOKEN)