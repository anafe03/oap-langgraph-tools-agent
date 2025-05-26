#!/bin/bash

# -----------------------------------
# CONFIGURATION
# -----------------------------------

BASE_URL="http://localhost:2024"
TOKEN=$(node get-token.js | grep 'ACCESS TOKEN:' | awk '{print $3}')

if [[ -z "$TOKEN" ]]; then
  echo "❌ Failed to get token from get-token.js"
  exit 1
fi

echo "🔐 Token obtained successfully"

# -----------------------------------
# Step 1: Check available graphs
# -----------------------------------
echo "🔍 Checking available graphs..."
GRAPHS_RESPONSE=$(curl -s -X GET "$BASE_URL/graphs" \
  -H "Authorization: Bearer $TOKEN")

echo "📊 Available graphs:"
echo "$GRAPHS_RESPONSE" | jq .

# Extract the first graph ID
GRAPH_ID=$(echo "$GRAPHS_RESPONSE" | jq -r '.graphs[0].graph_id')

if [[ -z "$GRAPH_ID" || "$GRAPH_ID" == "null" ]]; then
  echo "❌ No graphs found! Please create a graph first."
  exit 1
fi

echo "✅ Using graph ID: $GRAPH_ID"

# -----------------------------------
# Step 2: Create assistant with graph ID
# -----------------------------------
echo "🤖 Creating assistant using graph ID..."
ASSISTANT_RESPONSE=$(curl -s -X POST "$BASE_URL/assistants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{
    \"graph_id\": \"$GRAPH_ID\",
    \"config\": {
      \"configurable\": {
        \"model_name\": \"openai:gpt-4o\",
        \"temperature\": 0.7,
        \"max_tokens\": 4000,
        \"system_prompt\": \"You are a knowledgeable and supportive AI real estate agent named Vesty that helps homeowners navigate the For Sale By Owner (FSBO) process. Greet the user and introduce yourself. You have access to tools that let you create property listings, schedule showings, provide pricing guidance, and more. Use them when the users asks, before moving on with steps make sure to make the user aware of the next steps. Your goal is to assist sellers in effectively marketing and managing their property sale without needing a traditional agent.\"
      }
    },
    \"metadata\": {
      \"name\": \"Vesty Real Estate Agent\"
    }
  }")

echo "🧾 Assistant creation response:"
echo "$ASSISTANT_RESPONSE" | jq .

# Extract the assistant ID
ASSISTANT_ID=$(echo "$ASSISTANT_RESPONSE" | jq -r '.assistant_id')

if [[ -z "$ASSISTANT_ID" || "$ASSISTANT_ID" == "null" ]]; then
  echo "❌ Failed to create assistant!"
  exit 1
fi

echo "✅ Created assistant with ID: $ASSISTANT_ID"
echo ""
echo "🔷 Update your scripts with this assistant ID:"
echo "ASSISTANT_ID=\"$ASSISTANT_ID\""

# -----------------------------------
# Step 3: Test the assistant with a simple thread
# -----------------------------------
echo "🧵 Creating a thread to test the assistant..."
THREAD_RESPONSE=$(curl -s -X POST "$BASE_URL/threads" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{}')

THREAD_ID=$(echo "$THREAD_RESPONSE" | jq -r '.thread_id')

if [[ -z "$THREAD_ID" || "$THREAD_ID" == "null" ]]; then
  echo "❌ Failed to create thread!"
  exit 1
fi

echo "✅ Created thread with ID: $THREAD_ID"

# Send a test message
echo "📨 Sending a test message..."
curl -s -X POST "$BASE_URL/threads/$THREAD_ID/history" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "role": "user",
    "content": "Hi, I want to sell my house"
  }'

# Start a run with the assistant
echo "🚀 Starting a run with the assistant..."
RUN_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data "{
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"input\": {
      \"messages\": [
        {
          \"role\": \"user\",
          \"content\": \"Hi, I want to sell my house\"
        }
      ]
    }
  }")

echo "🧾 Run response:"
echo "$RUN_RESPONSE" | jq .

RUN_ID=$(echo "$RUN_RESPONSE" | jq -r '.run_id')

if [[ -z "$RUN_ID" || "$RUN_ID" == "null" ]]; then
  echo "❌ Failed to start run!"
  exit 1
fi

echo "✅ Started run with ID: $RUN_ID"

# Wait for the run to complete
echo "⏳ Waiting for response (this might take a moment)..."
MAX_ATTEMPTS=30
for ((i=1; i<=MAX_ATTEMPTS; i++)); do
  WAIT_RESPONSE=$(curl -s -X POST "$BASE_URL/threads/$THREAD_ID/runs/wait" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    --data "{
      \"assistant_id\": \"$ASSISTANT_ID\"
    }")
  
  if echo "$WAIT_RESPONSE" | grep -q "already running"; then
    echo "⏳ Still running... (attempt $i/$MAX_ATTEMPTS)"
    sleep 2
    continue
  fi
  
  # Check for response
  echo "📬 Response received:"
  echo "$WAIT_RESPONSE" | jq .
  
  # Try to extract the assistant message
  ASSISTANT_MSG=$(echo "$WAIT_RESPONSE" | jq -r '.messages[] | select(.role == "assistant") | .content' 2>/dev/null)
  if [[ -n "$ASSISTANT_MSG" ]]; then
    echo "🤖 Assistant replied:"
    echo "$ASSISTANT_MSG"
    break
  fi
  
  sleep 2
done

echo ""
echo "🔸 Setup complete! Use these values in your scripts:"
echo "ASSISTANT_ID=\"$ASSISTANT_ID\""
echo "Example thread ID: $THREAD_ID"