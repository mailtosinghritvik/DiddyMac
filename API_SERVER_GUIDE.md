# Bedrock AgentCore API Server Guide

## Quick Start

### Start the API Server

```bash
# Basic start
python bedrock_api_server.py

# Or with custom port
PORT=3000 python bedrock_api_server.py

# With API key authentication
API_KEY=your-secret-key python bedrock_api_server.py
```

The server will start on `http://localhost:8000` (or your specified port).

---

## API Endpoints

### 1. Health Check

```bash
GET http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T06:00:00"
}
```

### 2. Status

```bash
GET http://localhost:8000/status
```

Response:
```json
{
  "status": "running",
  "agent_id": "RitvikAgent-Nfl5014O49",
  "region": "us-west-2",
  "agent_runtime_arn": "arn:aws:bedrock-agentcore:...",
  "timestamp": "2025-11-12T06:00:00"
}
```

### 3. Invoke Agent (Standard Format)

```bash
POST http://localhost:8000/invoke
Content-Type: application/json

{
  "inputText": "Hello, how are you?",
  "sessionId": "optional-session-id"
}
```

Response:
```json
{
  "success": true,
  "completion": "Agent's response...",
  "session_id": "session-id-if-provided",
  "timestamp": "2025-11-12T06:00:00"
}
```

### 4. Invoke Agent (Custom Format)

```bash
POST http://localhost:8000/invoke/custom
Content-Type: application/json

{
  "prompt": "Schedule a meeting tomorrow at 3pm",
  "user": "user@example.com",
  "source": "api",
  "subject": "Meeting Request",
  "phone_number": "+1234567890",
  "sessionId": "optional-session-id"
}
```

### 5. Webhook Endpoint (Flexible)

```bash
POST http://localhost:8000/webhook
Content-Type: application/json

{
  "message": "Hello",
  "inputText": "Hello",
  "input": "Hello",
  "text": "Hello",
  "prompt": "Hello"
}
```

Accepts any JSON format and automatically extracts the input text.

---

## Authentication (Optional)

Set `API_KEY` environment variable to enable API key authentication:

```bash
export API_KEY=your-secret-key
python bedrock_api_server.py
```

Then include the API key in requests:

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-key" \
  -d '{"inputText": "Hello"}'
```

---

## Usage Examples

### Using curl

```bash
# Simple invoke
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Hello, how are you?"}'

# With session
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "inputText": "What is my name?",
    "sessionId": "your-session-id"
  }'

# Custom format
curl -X POST http://localhost:8000/invoke/custom \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Schedule a meeting",
    "user": "user@example.com",
    "source": "api"
  }'
```

### Using Python requests

```python
import requests

# Simple invoke
response = requests.post(
    'http://localhost:8000/invoke',
    json={'inputText': 'Hello, how are you?'}
)
print(response.json())

# With session
response = requests.post(
    'http://localhost:8000/invoke',
    json={
        'inputText': 'What is my name?',
        'sessionId': 'your-session-id'
    }
)
print(response.json())
```

### Using JavaScript/fetch

```javascript
// Simple invoke
fetch('http://localhost:8000/invoke', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    inputText: 'Hello, how are you?'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## Deployment

### Local Development

```bash
python bedrock_api_server.py
```

### Production (with gunicorn)

```bash
pip install gunicorn
gunicorn bedrock_api_server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "bedrock_api_server.py"]
```

### Railway/Heroku

The server will automatically use the `PORT` environment variable.

```bash
# Railway
railway up

# Heroku
heroku create your-api-name
git push heroku main
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8000` |
| `API_PORT` | Alternative port variable | `8000` |
| `API_KEY` | API key for authentication (optional) | `None` |

---

## Error Handling

All endpoints return consistent error format:

```json
{
  "success": false,
  "error": "Error message",
  "timestamp": "2025-11-12T06:00:00"
}
```

HTTP status codes:
- `200` - Success
- `400` - Bad request
- `401` - Unauthorized (if API key is set and invalid)
- `500` - Server error

---

## CORS

CORS is enabled by default for all origins. For production, configure:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## Testing

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Status
curl http://localhost:8000/status

# Invoke
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"inputText": "Test message"}'
```

### Test Script

```python
# test_api.py
import requests

# Test health
response = requests.get('http://localhost:8000/health')
print("Health:", response.json())

# Test invoke
response = requests.post(
    'http://localhost:8000/invoke',
    json={'inputText': 'Hello, test'}
)
print("Invoke:", response.json())
```

---

## Integration Examples

### Zapier Webhook

1. Deploy API server to Railway/Heroku
2. Use endpoint: `https://your-api.railway.app/webhook`
3. Configure Zapier to POST to this URL

### Make.com (Integromat)

1. Use HTTP module
2. URL: `https://your-api.railway.app/invoke`
3. Method: POST
4. Body: `{"inputText": "{{webhook.message}}"}`

### n8n

1. Create HTTP Request node
2. URL: `https://your-api.railway.app/invoke`
3. Method: POST
4. Body: JSON with `inputText`

---

## Monitoring

The API logs all requests. Check logs for:
- Request/response details
- Errors and exceptions
- Performance metrics

---

## Security Recommendations

1. **Enable API Key**: Set `API_KEY` environment variable
2. **Use HTTPS**: Deploy behind HTTPS (Railway/Heroku provide this)
3. **Rate Limiting**: Add rate limiting for production
4. **CORS**: Configure specific origins instead of `*`
5. **Input Validation**: Already handled by Pydantic models

---

## Next Steps

1. Start the server: `python bedrock_api_server.py`
2. Test endpoints with curl or Postman
3. Deploy to Railway/Heroku for production
4. Use the API URL in your webhooks/integrations

---

## Troubleshooting

### Port already in use
```bash
# Use different port
PORT=3000 python bedrock_api_server.py
```

### API key not working
- Check `X-API-Key` header is included
- Verify `API_KEY` environment variable matches

### Agent not responding
- Check AWS credentials are configured
- Verify agent is deployed: `agentcore status --agent RitvikAgent`
- Check CloudWatch logs for agent errors

---

## Summary

✅ **Simple REST API** - Easy to use HTTP endpoints  
✅ **Multiple formats** - Standard and custom request formats  
✅ **Webhook ready** - Flexible webhook endpoint  
✅ **Optional auth** - API key authentication  
✅ **Production ready** - Deploy to Railway/Heroku  

Your API is ready to use! 🚀

