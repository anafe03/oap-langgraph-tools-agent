#!/bin/bash

# -----------------------------------
# CONFIGURATION
# -----------------------------------

BASE_URL="http://localhost:2024"
TOKEN=$(node get-token.js | grep 'ACCESS TOKEN:' | awk '{print $3}') # Extract token from get-token.js output
ASSISTANT_ID="e878fafe-dace-4935-99db-ffbe0cee5b6e"
MODEL="openai:gpt-4o"
USER_ID="f0a916ec-cb6e-4733-a43c-ad5847ed016f"


echo "🤖 GPT Assistant: Hello! Type 'exit' to quit."

# -----------------------------
# STEP 1: Create a Thread
# -----------------------------
echo "🔹 Creating thread..."
THREAD_RESPONSE=$(curl -s -X POST "$BASE_URL/threads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{}')

echo "📦 Thread creation response: $THREAD_RESPONSE"

THREAD_ID=$(echo "$THREAD_RESPONSE" | jq -r '.thread_id')

if [[ -z "$THREAD_ID" || "$THREAD_ID" == "null" ]]; then
  echo "❌ Failed to create thread:"
  echo "$THREAD_RESPONSE"
  exit 1 
fi

echo "✅ Thread ID: $THREAD_ID"

# -----------------------------
# CHAT LOOP
# -----------------------------
while true; do
  echo
  read -p "👤 You: " USER_MESSAGE

  if [[ "$USER_MESSAGE" == "exit" ]]; then
    echo "👋 Ending chat."
    break
  fi

  echo "📨 Posting message to thread..."
  POST_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/history" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
      \"role\": \"user\",
      \"content\": \"$USER_MESSAGE\"
    }")
  echo "📩 Post message response: $POST_RESPONSE"

  echo "🚀 Starting assistant run..."
  RUN_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
      \"assistant_id\": \"$ASSISTANT_ID\",
      \"input\": {
        \"messages\": [
          {
            \"role\": \"user\",
            \"content\": \"$USER_MESSAGE\"
          }
        ]
      }
    }")

  echo "🧾 Run started: $RUN_RESPONSE"
  RUN_ID=$(echo "$RUN_RESPONSE" | jq -r '.run_id')

  if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
    echo "❌ Failed to start run. Full response:"
    echo "$RUN_RESPONSE"
    continue
  fi

  echo "🧠 Assistant is thinking..."
  while true; do
    WAIT_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs/wait" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      --data "{
        \"assistant_id\": \"$ASSISTANT_ID\"
      }")

    echo "📬 Wait response: $WAIT_RESPONSE"

    MESSAGES=$(echo "$WAIT_RESPONSE" | jq -r '.messages | select(type == "array") | .[]?.content')
    TOOLS_USED=$(echo "$WAIT_RESPONSE" | jq -r '.tool_calls | select(. != null) | .[]?.name')

    if [[ -n "$MESSAGES" ]]; then
      echo "🤖 Assistant:"
      echo "$MESSAGES"
      if [[ -n "$TOOLS_USED" ]]; then
        echo "🛠️ Tool(s) invoked: $TOOLS_USED"
      fi
      break
    elif echo "$WAIT_RESPONSE" | grep -q "Thread is already running"; then
      echo "⏳ Still running. Retrying in 2s..."
      sleep 2
    else
      echo "❌ Unexpected response:"
      echo "$WAIT_RESPONSE" | jq
      break
    fi
  done
done
