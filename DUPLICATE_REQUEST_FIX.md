# Duplicate Request Processing Fix

## Problem
`process_request_async` was being called multiple times for the same request, causing:
- Duplicate API calls and processing
- Multiple WhatsApp/email confirmations sent
- Wasted resources and potential infinite loops
- Confusion in logs

## Root Causes Identified

### 1. Server Auto-Start Issue (agent.py)
**Problem**: The server was starting both when run as `__main__` AND when imported as a module.

```python
# OLD CODE (PROBLEMATIC)
if __name__ == "__main__":
    start_server()
else:
    # This was causing issues!
    logger.info("Running as module (python -m agent), starting server...")
    start_server()
```

**Fix**: Only start server when explicitly run:

```python
# NEW CODE (FIXED)
if __name__ == "__main__" or __name__ == "__mp_main__":
    start_server()
```

### 2. No Request Deduplication
**Problem**: No mechanism to detect and prevent duplicate request processing.

**Fix**: Implemented request deduplication with:
- Request hashing based on user, input, source, subject, and timestamp
- In-memory cache tracking recently processed requests (5-minute window)
- Automatic cleanup of expired cache entries
- Unique request IDs for tracking

## Implementation Details

### Request Deduplication System

1. **Request Hash Generation**
   - Creates MD5 hash from key fields: user, input, source, subject, timestamp
   - Timestamp rounded to nearest 10 seconds to catch near-simultaneous duplicates

2. **Deduplication Cache**
   - In-memory dictionary: `{request_hash: processing_timestamp}`
   - 5-minute retention window (configurable via `DEDUP_WINDOW_SECONDS`)
   - Thread-safe with asyncio locks

3. **Request ID Tracking**
   - Each request gets unique UUID (8-char short form)
   - Logged at start of processing for debugging
   - Format: `🔵 REQUEST ID: a1b2c3d4 | Hash: e5f6g7h8`

### Behavior

When duplicate detected:
```json
{
  "status": "skipped",
  "reason": "duplicate_request",
  "message": "Request already processed 15.2 seconds ago",
  "request_id": "a1b2c3d4",
  "request_hash": "e5f6g7h8",
  "original_processing_time": "2025-11-13T10:30:45.123456"
}
```

## Files Modified

1. **agent.py**
   - Fixed server auto-start logic (lines 297-302)
   - Removed else-block that started server on module import

2. **main.py**
   - Added imports: hashlib, uuid, timedelta, defaultdict
   - Added global deduplication cache and lock
   - Added `_generate_request_hash()` function
   - Added `_cleanup_old_requests()` function
   - Modified `process_request_async()` to check for duplicates
   - Added unique request ID logging

3. **check_running_processes.ps1** (NEW)
   - PowerShell script to detect running Python/server processes
   - Identifies processes on ports 8000 and 8080
   - Provides commands to kill duplicate processes

## How to Use

### Check for Running Processes
```powershell
powershell -ExecutionPolicy Bypass -File check_running_processes.ps1
```

### Start Only ONE Server

**For AWS Bedrock Agent Core:**
```bash
python agent.py
```

**For Webhook Server:**
```bash
python webhook_server.py
```

**For API Server:**
```bash
python bedrock_api_server.py
```

### Monitor for Duplicates

Look for these log messages:

**Normal Processing:**
```
🔵 REQUEST ID: a1b2c3d4 | Hash: e5f6g7h8
=== STARTING REQUEST PROCESSING ===
```

**Duplicate Detected:**
```
⚠️  DUPLICATE REQUEST DETECTED (ID: x9y8z7w6, Hash: v5u4t3s2)
   Request was processed 15.2 seconds ago - SKIPPING to prevent duplicate execution
```

## Configuration

### Adjust Deduplication Window

In `main.py`:
```python
DEDUP_WINDOW_SECONDS = 300  # 5 minutes (default)
# Change to smaller value for stricter deduplication:
DEDUP_WINDOW_SECONDS = 60   # 1 minute
# Or larger value for longer protection:
DEDUP_WINDOW_SECONDS = 600  # 10 minutes
```

## Testing

### Test Duplicate Detection

Send the same request twice within 5 minutes:

```python
import asyncio
from main import process_request_async

test_input = {
    "user": "test@example.com",
    "source": "email",
    "input": "Test message",
    "subject": "Test",
    "created_at": "2025-11-13T10:30:00Z"
}

# First call - should process
result1 = asyncio.run(process_request_async(test_input))
print(result1)  # Normal processing

# Second call - should be skipped as duplicate
result2 = asyncio.run(process_request_async(test_input))
print(result2)  # {"status": "skipped", "reason": "duplicate_request", ...}
```

## Benefits

1. **Prevents Duplicate Processing**
   - Saves API costs (OpenAI, WhatsApp API)
   - Prevents duplicate messages sent to users
   - Reduces server load

2. **Better Debugging**
   - Unique request IDs for tracking
   - Clear log messages when duplicates detected
   - Request hashes for correlation

3. **Automatic Cleanup**
   - Old cache entries automatically removed
   - No memory leaks from long-running processes
   - Configurable retention window

4. **Thread-Safe**
   - Uses asyncio locks for concurrent request handling
   - Safe for multiple simultaneous requests

## Limitations

1. **In-Memory Only**
   - Cache cleared on server restart
   - Not shared across multiple server instances
   - For distributed systems, consider Redis or database-backed deduplication

2. **Time-Based Window**
   - Only prevents duplicates within configured window
   - Different timestamps create different hashes
   - Very rare edge cases with exact timestamp matches

## Future Improvements

1. **Persistent Cache**
   - Store in Redis or database for multi-instance deployments
   - Survive server restarts

2. **Metrics/Monitoring**
   - Track duplicate rate
   - Alert on excessive duplicates (possible bug/attack)

3. **Configurable Hash Fields**
   - Allow customization of what fields determine uniqueness
   - Different strategies for different request types

## Troubleshooting

### Still seeing duplicates?

1. **Check for multiple running servers:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File check_running_processes.ps1
   ```

2. **Check logs for request IDs:**
   - Different request IDs = different requests
   - Same request ID = investigate why function called multiple times

3. **Check if requests have different timestamps:**
   - Requests with very different timestamps won't be detected as duplicates
   - Adjust `DEDUP_WINDOW_SECONDS` if needed

4. **Check webhook configuration:**
   - Ensure Supabase webhook not configured multiple times
   - Check for duplicate triggers on the same table

### Clear deduplication cache

Restart the server:
```bash
# Kill process
Ctrl+C

# Restart
python agent.py
```

## Summary

The fix implements a robust deduplication system that:
- ✅ Prevents duplicate request processing
- ✅ Provides clear logging and tracking
- ✅ Automatically cleans up old entries
- ✅ Thread-safe for concurrent requests
- ✅ Configurable retention window
- ✅ Fixed server auto-start issue

Your system should now process each unique request exactly once!

