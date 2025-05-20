#!/bin/bash

# -----------------------------------
# CONFIGURATION
# -----------------------------------

BASE_URL="http://localhost:2024"
TOKEN="eyJhbGciOiJIUzI1NiIsImtpZCI6IkdEejRHRFlVR2ludWE2YlAiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2dkbWR1cnphZWV6Y3Jncm10YWJ4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJmMGE5MTZlYy1jYjZlLTQ3MzMtYTQzYy1hZDU4NDdlZDAxNmYiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzQ3Njg3MjgyLCJpYXQiOjE3NDc2ODM2ODIsImVtYWlsIjoiYXVzdGlubmFmZUBhb2wuY29tIiwicGhvbmUiOiIiLCJhcHBfbWV0YWRhdGEiOnsicHJvdmlkZXIiOiJlbWFpbCIsInByb3ZpZGVycyI6WyJlbWFpbCJdfSwidXNlcl9tZXRhZGF0YSI6eyJlbWFpbF92ZXJpZmllZCI6dHJ1ZX0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NDc2ODM2ODJ9XSwic2Vzc2lvbl9pZCI6IjM4MjRiYjA4LWIxYzItNDlkMi04ZjMwLTU4ZmFhYzFlNWVmMCIsImlzX2Fub255bW91cyI6ZmFsc2V9.s2cnMGbbr8ERfliLMNhbwON8RFf3ulwqi6ghPoV4naw"

ASSISTANT_ID="e878fafe-dace-4935-99db-ffbe0cee5b6e"
THREAD_ID="b6e90eeb-151e-4af8-af6d-db75795b265e"
USER_ID="f0a916ec-cb6e-4733-a43c-ad5847ed016f"
MODEL="openai:gpt-4o"
REQ_ID=$(uuidgen)

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
# STEP 2: Post User Message
# -----------------------------------

echo "🔹 Posting message to thread..."
curl -s -X POST "$BASE_URL/threads/$THREAD_ID/history" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{
    \"role\": \"user\",
    \"content\": \"What is the GDP of the UK over the last 5 years?\"
  }" > /dev/null

# -----------------------------------
# STEP 3: Start Assistant Run
# -----------------------------------

echo "🔹 Starting assistant run..."
RUN_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"input\": {
      \"messages\": [
        {
          \"role\": \"user\",
          \"content\": \"Can you chart UK GDP over the past 5 years?\"
        }
      ]
    }
  }")


RUN_ID=$(echo "$RUN_RESPONSE" | jq -r '.run_id')

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "❌ Failed to start run. Full response:"
  echo "$RUN_RESPONSE"
  exit 1
fi

echo "✅ Run started: $RUN_ID"

# -----------------------------------
# STEP 4: Wait for Assistant Response
# -----------------------------------

echo "🔹 Waiting for assistant response..."

while true; do
  WAIT_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs/wait" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
      \"assistant_id\": \"$ASSISTANT_ID\"
    }")

  MESSAGES=$(echo "$WAIT_RESPONSE" | jq -r '.messages | select(type == "array") | .[]?.content')

  if [[ -n "$MESSAGES" ]]; then
    echo "✅ Assistant response:"
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
