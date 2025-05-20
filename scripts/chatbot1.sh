#!/bin/bash

# -----------------------------------
# CONFIGURATION
# -----------------------------------

BASE_URL="http://localhost:2024"
TOKEN="eyJhbGciOiJIUzI1NiIsImtpZCI6IkdEejRHRFlVR2ludWE2YlAiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2dkbWR1cnphZWV6Y3Jncm10YWJ4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJmMGE5MTZlYy1jYjZlLTQ3MzMtYTQzYy1hZDU4NDdlZDAxNmYiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ3NjkxMDU4LCJpYXQiOjE3NDc2ODc0NTgsImVtYWlsIjoiYXVzdGlubmFmZUBhb2wuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NDc2ODc0NTh9XSwic2Vzc2lvbl9pZCI6IjZkNmIyZjU1LWIwODMtNGQ3MC04MWU4LTdkYWQ2Y2JmNTBjNyIsImlzX2Fub255bW91cyI6ZmFsc2V9.nqPlCkDvUKZNGnmY_gEgt6dioy3N6ePif08BtWmqvn0"
ASSISTANT_ID="e878fafe-dace-4935-99db-ffbe0cee5b6e"
MODEL="openai:gpt-4o"
USER_ID="f0a916ec-cb6e-4733-a43c-ad5847ed016f"

echo "🤖 GPT Assistant: Hello! Type 'exit' to quit."


# -----------------------------------
# STEP 1: Create a Thread
# -----------------------------------

echo "🔹 Creating thread..."
THREAD_RESPONSE=$(curl -s -X POST "$BASE_URL/threads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{}')

THREAD_ID=$(echo "$THREAD_RESPONSE" | jq -r '.thread_id')

if [[ -z "$THREAD_ID" || "$THREAD_ID" == "null" ]]; then
  echo "❌ Failed to create thread:"
  echo "$THREAD_RESPONSE"
  exit 1
fi

echo "✅ Thread ID: $THREAD_ID"

# -----------------------------------
# CHAT LOOP
# -----------------------------------

while true; do
  echo
  read -p "👤 You: " USER_MESSAGE

  if [[ "$USER_MESSAGE" == "exit" ]]; then
    echo "👋 Ending chat."
    break
  fi

  echo "📨 Sending your message..."
  echo "🔎 [DEBUG] Message content: $USER_MESSAGE"  # 👉 [DEBUG]

  # Step 2: Post user message to thread
  curl -s -X POST "$BASE_URL/threads/$THREAD_ID/history" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
      \"role\": \"user\",
      \"content\": \"$USER_MESSAGE\"
    }" > /dev/null

  # Step 3: Start a run
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

  RUN_ID=$(echo "$RUN_RESPONSE" | jq -r '.run_id')
  echo "🔎 [DEBUG] Run response: $RUN_RESPONSE"  # 👉 [DEBUG]

  if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
    echo "❌ Failed to start run. Full response:"
    echo "$RUN_RESPONSE"
    continue
  fi

  echo "🧠 Assistant is thinking... (Run ID: $RUN_ID)"  # 👉 [DEBUG]

  # Step 4: Wait for assistant response
  while true; do
    WAIT_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs/wait" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      --data "{
        \"assistant_id\": \"$ASSISTANT_ID\"
      }")

    echo "🔎 [DEBUG] Wait response: $WAIT_RESPONSE"  # 👉 [DEBUG]

    # Try to detect tool usage
    TOOL_CALLS=$(echo "$WAIT_RESPONSE" | jq -r '.tool_calls[]?.tool_name')
    if [[ -n "$TOOL_CALLS" ]]; then
      echo "🛠️ [DEBUG] Tool(s) used in run: $TOOL_CALLS"
    fi

    MESSAGES=$(echo "$WAIT_RESPONSE" | jq -r '.messages | select(type == "array") | .[]?.content')

    if [[ -n "$MESSAGES" ]]; then
      echo "🤖 Assistant:"
      echo "$MESSAGES"
      break
    elif echo "$WAIT_RESPONSE" | grep -q "Thread is already running"; then
      echo "⏳ Still running. Retrying in 2 seconds..."
      sleep 2
    else
      echo "❌ Unexpected response:"
      echo "$WAIT_RESPONSE" | jq
      break
    fi
  done
done
