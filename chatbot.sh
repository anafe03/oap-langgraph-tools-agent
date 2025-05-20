#!/bin/bash

# -----------------------------------
# CONFIGURATION
# -----------------------------------

BASE_URL="http://localhost:2024"
TOKEN="eyJhbGciOiJIUzI1NiIsImtpZCI6IkdEejRHRFlVR2ludWE2YlAiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2dkbWR1cnphZWV6Y3Jncm10YWJ4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJmMGE5MTZlYy1jYjZlLTQ3MzMtYTQzYy1hZDU4NDdlZDAxNmYiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ3NzU4MjYyLCJpYXQiOjE3NDc3NTQ2NjIsImVtYWlsIjoiYXVzdGlubmFmZUBhb2wuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NDc3NTQ2NjJ9XSwic2Vzc2lvbl9pZCI6IjQ4NDRmMmVhLTE4NTYtNDgwNC04ZjJjLTIyMzZiNzI5NTAzOCIsImlzX2Fub255bW91cyI6ZmFsc2V9.slqP_apFrNlUyGTOeRvO4jlvZF_mNgFef7_FlMB6Go4"
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

  # Step 2: Post user message to thread
  echo "📨 Sending your message..."
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

  if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
    echo "❌ Failed to start run. Full response:"
    echo "$RUN_RESPONSE"
    continue
  fi

  echo "🧠 Assistant is thinking..."

  # Step 4: Wait for assistant response
  while true; do
    WAIT_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs/wait" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      --data "{
        \"assistant_id\": \"$ASSISTANT_ID\"
      }")

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
