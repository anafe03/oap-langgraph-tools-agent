#!/usr/bin/env python
"""
Simple script to test if your LangGraph server is working correctly.
This script:
1. Gets a token using your get-token.js script
2. Lists available assistants
3. Creates a test thread
4. Sends a simple message
5. Gets the response

Usage:
python test_langgraph_server.py
"""

import subprocess
import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:2024"
ASSISTANT_ID = None  # Will be set dynamically if available

def get_token():
    """Get token from get-token.js script"""
    try:
        result = subprocess.run(
            ["node", "get-token.js"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        output = result.stdout
        token_line = [line for line in output.split('\n') if 'ACCESS TOKEN:' in line]
        if token_line:
            token = token_line[0].split('ACCESS TOKEN:')[1].strip()
            return token
        else:
            print("❌ Could not extract token from get-token.js output")
            print(f"Output was: {output}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running get-token.js: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error getting token: {e}")
        return None

def main():
    # Step 1: Get token
    print("🔑 Getting token...")
    token = get_token()
    if not token:
        print("❌ Failed to get token. Exiting.")
        sys.exit(1)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Check server health
    print("\n🏥 Checking server health...")
    try:
        health_resp = requests.get(f"{BASE_URL}/health", headers=headers)
        if health_resp.status_code == 200:
            print("✅ Server is healthy")
        else:
            print(f"⚠️ Server health check returned: {health_resp.status_code}")
            print(health_resp.text)
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        sys.exit(1)
    
    # Step 3: List assistants
    print("\n📋 Listing available assistants...")
    try:
        assistants_resp = requests.post(
            f"{BASE_URL}/assistants/search",
            headers=headers,
            json={}
        )
        
        if assistants_resp.status_code != 200:
            print(f"❌ Failed to list assistants: {assistants_resp.status_code}")
            print(assistants_resp.text)
        else:
            assistants = assistants_resp.json().get("assistants", [])
            if not assistants:
                print("ℹ️ No assistants found")
            else:
                print(f"✅ Found {len(assistants)} assistants:")
                for i, assistant in enumerate(assistants, 1):
                    assistant_id = assistant.get("assistant_id")
                    name = assistant.get("metadata", {}).get("name", "Unnamed")
                    print(f"  {i}. ID: {assistant_id} | Name: {name}")
                    
                    # Use the first assistant for testing
                    if i == 1:
                        global ASSISTANT_ID
                        ASSISTANT_ID = assistant_id
    except Exception as e:
        print(f"❌ Error listing assistants: {e}")
    
    # Step 4: Create a test assistant if none found
    if not ASSISTANT_ID:
        print("\n🤖 No assistants found. Creating a test assistant...")
        try:
            create_resp = requests.post(
                f"{BASE_URL}/assistants",
                headers=headers,
                json={
                    "config": {
                        "configurable": {
                            "model_name": "openai:gpt-4o",
                            "temperature": 0.7,
                            "max_tokens": 1000,
                            "system_prompt": "You are a helpful assistant."
                        }
                    },
                    "metadata": {
                        "name": "Test Assistant"
                    }
                }
            )
            
            if create_resp.status_code != 200:
                print(f"❌ Failed to create assistant: {create_resp.status_code}")
                print(create_resp.text)
            else:
                ASSISTANT_ID = create_resp.json().get("assistant_id")
                print(f"✅ Created test assistant with ID: {ASSISTANT_ID}")
        except Exception as e:
            print(f"❌ Error creating assistant: {e}")
    
    if not ASSISTANT_ID:
        print("❌ No assistant ID available for testing. Exiting.")
        sys.exit(1)
    
    # Step 5: Create a thread
    print("\n🧵 Creating a thread...")
    try:
        thread_resp = requests.post(
            f"{BASE_URL}/threads",
            headers=headers,
            json={}
        )
        
        if thread_resp.status_code != 200:
            print(f"❌ Failed to create thread: {thread_resp.status_code}")
            print(thread_resp.text)
            sys.exit(1)
        
        thread_id = thread_resp.json().get("thread_id")
        print(f"✅ Created thread with ID: {thread_id}")
        
        # Step 6: Send a message
        print("\n📨 Posting a test message...")
        post_resp = requests.post(
            f"{BASE_URL}/threads/{thread_id}/history",
            headers=headers,
            json={
                "role": "user",
                "content": "Hello, this is a test message."
            }
        )
        
        if post_resp.status_code != 200:
            print(f"❌ Failed to post message: {post_resp.status_code}")
            print(post_resp.text)
        else:
            print("✅ Message posted successfully")
        
        # Step 7: Start a run
        print("\n🚀 Starting a run...")
        run_resp = requests.post(
            f"{BASE_URL}/threads/{thread_id}/runs",
            headers=headers,
            json={
                "assistant_id": ASSISTANT_ID,
                "input": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello, this is a test message."
                        }
                    ]
                }
            }
        )
        
        if run_resp.status_code != 200:
            print(f"❌ Failed to start run: {run_resp.status_code}")
            print(run_resp.text)
            sys.exit(1)
        
        run_id = run_resp.json().get("run_id")
        print(f"✅ Started run with ID: {run_id}")
        
        # Step 8: Wait for the run to complete
        print("\n⏳ Waiting for response...")
        max_attempts = 30
        for attempt in range(max_attempts):
            wait_resp = requests.post(
                f"{BASE_URL}/threads/{thread_id}/runs/wait",
                headers=headers,
                json={"assistant_id": ASSISTANT_ID}
            )
            
            if wait_resp.status_code != 200:
                if "already running" in wait_resp.text.lower():
                    print(f"  Still running... (attempt {attempt+1}/{max_attempts})")
                    time.sleep(1)
                    continue
                else:
                    print(f"❌ Wait request failed: {wait_resp.status_code}")
                    print(wait_resp.text)
                    break
            
            try:
                wait_data = wait_resp.json()
                messages = wait_data.get("messages", [])
                
                if messages:
                    # Find the latest assistant message
                    assistant_response = None
                    for msg in reversed(messages):
                        if isinstance(msg, dict) and msg.get("role") == "assistant":
                            assistant_response = msg.get("content", "")
                            break
                    
                    if assistant_response:
                        print("\n🤖 Assistant response:")
                        print(f"  {assistant_response}")
                        break
            except Exception as e:
                print(f"❌ Error parsing wait response: {e}")
            
            time.sleep(1)
        else:
            print("❌ Timed out waiting for assistant response")
        
        # Step 9: Clean up
        print("\n🧹 Cleaning up...")
        delete_resp = requests.delete(
            f"{BASE_URL}/threads/{thread_id}",
            headers=headers
        )
        
        if delete_resp.status_code in [200, 204, 404]:
            print(f"✅ Thread deleted successfully")
        else:
            print(f"⚠️ Failed to delete thread: {delete_resp.status_code}")
            print(delete_resp.text)
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    main()