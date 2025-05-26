#!/bin/bash

BASE_URL="http://localhost:2024"
TOKEN=$(node get-token.js | grep 'ACCESS TOKEN:' | awk '{print $3}')
ASSISTANT_NAME="My New Assistant"
GRAPH_ID="agent"

echo "🔍 Using token: ${TOKEN:0:20}..."

# Fetch existing assistants using the correct search endpoint
EXISTING_ASSISTANTS=$(curl -s -X POST "$BASE_URL/assistants/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "limit": 100,
    "offset": 0
  }')

echo "📋 Search response: $EXISTING_ASSISTANTS"

# Try to find assistant ID by name
ASSISTANT_ID=$(echo "$EXISTING_ASSISTANTS" | jq -r "map(select(.name == \"$ASSISTANT_NAME\")) | .[0].assistant_id // empty")

# Create assistant if not found
if [[ -z "$ASSISTANT_ID" || "$ASSISTANT_ID" == "null" ]]; then
  echo "🆕 Creating assistant '$ASSISTANT_NAME'..."
  
  CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/assistants" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
      \"graph_id\": \"$GRAPH_ID\",
      \"config\": {},
      \"metadata\": {},
      \"if_exists\": \"do_nothing\",
      \"name\": \"$ASSISTANT_NAME\",
      \"description\": \"Created via Bash script\"
    }")
  
  echo "📝 Create response: $CREATE_RESPONSE"
  ASSISTANT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.assistant_id')
  
  if [[ -z "$ASSISTANT_ID" || "$ASSISTANT_ID" == "null" ]]; then
    echo "❌ Failed to create assistant."
    echo "$CREATE_RESPONSE"
    exit 1
  fi
  
  echo "✅ Assistant created with ID: $ASSISTANT_ID"
else
  echo "✅ Found existing assistant: $ASSISTANT_NAME (ID: $ASSISTANT_ID)"
fi

# Create thread
THREAD_RESPONSE=$(curl -s -X POST "$BASE_URL/threads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{}')

THREAD_ID=$(echo "$THREAD_RESPONSE" | jq -r '.thread_id')
echo "💬 Created thread: $THREAD_ID"

# Function to get thread state and extract messages
get_latest_response() {
  local thread_id=$1
  
  # Get the current thread state
  STATE_RESPONSE=$(curl -s -X GET "$BASE_URL/threads/$thread_id/state" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "🔍 Debug - Thread state response:" >&2
  echo "$STATE_RESPONSE" | jq '.' >&2
  
  # Try different ways to extract messages based on actual structure
  RESPONSE=""
  
  # Method 1: Check if values is an array with messages
  RESPONSE=$(echo "$STATE_RESPONSE" | jq -r '.values[0].messages[]? | select(.role == "assistant") | .content' 2>/dev/null | tail -1)
  
  # Method 2: Check if values is an object with messages
  if [[ -z "$RESPONSE" || "$RESPONSE" == "null" ]]; then
    RESPONSE=$(echo "$STATE_RESPONSE" | jq -r '.values.messages[]? | select(.role == "assistant") | .content' 2>/dev/null | tail -1)
  fi
  
  # Method 3: Check if messages are directly in values
  if [[ -z "$RESPONSE" || "$RESPONSE" == "null" ]]; then
    RESPONSE=$(echo "$STATE_RESPONSE" | jq -r '.values[] | select(.role == "assistant") | .content' 2>/dev/null | tail -1)
  fi
  
  # Method 4: Look for any content field in the response
  if [[ -z "$RESPONSE" || "$RESPONSE" == "null" ]]; then
    RESPONSE=$(echo "$STATE_RESPONSE" | jq -r '.. | .content? // empty' 2>/dev/null | grep -v "^$" | tail -1)
  fi
  
  echo "$RESPONSE"
}

# Chat loop
while true; do
  echo
  read -p "👤 You: " USER_MESSAGE
  if [[ "$USER_MESSAGE" == "exit" ]]; then break; fi
  
  echo "🚀 Running assistant..."
  
  # Start a run with the user message
  RUN_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
      \"assistant_id\": \"$ASSISTANT_ID\",
      \"input\": {
        \"messages\": [
          { \"role\": \"user\", \"content\": \"$USER_MESSAGE\" }
        ]
      }
    }")
  
  RUN_ID=$(echo "$RUN_RESPONSE" | jq -r '.run_id')
  echo "📝 Started run: $RUN_ID"
  
  # Wait for the run to complete
  echo "⏳ Waiting for assistant to respond..."
  
  MAX_ATTEMPTS=30
  ATTEMPT=0
  
  while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    RUN_CHECK=$(curl -s -X GET "$BASE_URL/threads/$THREAD_ID/runs/$RUN_ID" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "🔍 Debug - Run status response:" >&2
    echo "$RUN_CHECK" | jq '.' >&2
    
    RUN_STATUS=$(echo "$RUN_CHECK" | jq -r '.status // "unknown"')
    echo "📊 Run status: $RUN_STATUS" >&2
    
    if [[ "$RUN_STATUS" == "success" ]]; then
      echo "✅ Run completed successfully!" >&2
      break
    elif [[ "$RUN_STATUS" == "error" ]]; then
      echo "❌ Run failed" >&2
      echo "$RUN_CHECK" | jq '.error // "Unknown error"' >&2
      break
    elif [[ "$RUN_STATUS" == "unknown" ]]; then
      echo "⚠️ Unable to get run status, continuing anyway..." >&2
      break
    else
      echo "⏳ Status: $RUN_STATUS, waiting..." >&2
      sleep 2
      ((ATTEMPT++))
    fi
  done
  
  if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "⏰ Timeout waiting for run to complete" >&2
  fi
  
  # Get the assistant's response
  RESPONSE=$(get_latest_response "$THREAD_ID")
  
  if [[ -n "$RESPONSE" && "$RESPONSE" != "null" ]]; then
    echo -e "🤖 Assistant: $RESPONSE"
  else
    echo "🤖 Assistant: [No response received]"
  fi
done

echo "👋 Chat ended."