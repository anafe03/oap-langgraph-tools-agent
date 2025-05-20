// chat-interface.js
import fetch from 'node-fetch'

const BASE_URL = 'http://localhost:2024'
const ASSISTANT_ID = 'YOUR_ASSISTANT_ID'
const TOKEN = process.env.USER_JWT_ACCESS_TOKEN // From .env

export async function runChat(message) {
  const headers = {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json',
  }

  const threadRes = await fetch(`${BASE_URL}/threads`, {
    method: 'POST',
    headers,
    body: JSON.stringify({})
  })
  const { thread_id } = await threadRes.json()

  await fetch(`${BASE_URL}/threads/${thread_id}/history`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      role: 'user',
      content: message
    }),
  })

  const runRes = await fetch(`${BASE_URL}/threads/${thread_id}/runs`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ assistant_id: ASSISTANT_ID })
  })
  const { run_id } = await runRes.json()

  let reply = ''
  while (true) {
    const waitRes = await fetch(`${BASE_URL}/threads/${thread_id}/runs/wait`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ assistant_id: ASSISTANT_ID })
    })
    const json = await waitRes.json()

    if (Array.isArray(json.messages)) {
      reply = json.messages.map(m => m.content).join('\n')
      break
    }
    await new Promise(res => setTimeout(res, 1000))
  }

  return reply
}
