"""
Test script to verify request deduplication is working correctly
"""
import asyncio
from datetime import datetime
from main import process_request_async

async def test_deduplication():
    """Test that duplicate requests are properly detected and skipped"""
    
    print("=" * 80)
    print("TESTING REQUEST DEDUPLICATION")
    print("=" * 80)
    
    # Test input
    test_input = {
        "user": "test@example.com",
        "source": "email",
        "input": "This is a test message to check deduplication",
        "subject": "Test Subject",
        "created_at": datetime.now().isoformat()
    }
    
    print("\n1. First Request (should process normally):")
    print("-" * 80)
    result1 = await process_request_async(test_input)
    print(f"\nResult 1 Status: {result1.get('status')}")
    if result1.get('request_id'):
        print(f"Request ID: {result1.get('request_id')}")
        print(f"Request Hash: {result1.get('request_hash')}")
    
    print("\n\n2. Second Request - SAME INPUT (should be skipped as duplicate):")
    print("-" * 80)
    result2 = await process_request_async(test_input)
    print(f"\nResult 2 Status: {result2.get('status')}")
    print(f"Reason: {result2.get('reason', 'N/A')}")
    print(f"Message: {result2.get('message', 'N/A')}")
    if result2.get('request_id'):
        print(f"Request ID: {result2.get('request_id')}")
        print(f"Request Hash: {result2.get('request_hash')}")
    
    # Verify deduplication worked
    if result2.get('status') == 'skipped' and result2.get('reason') == 'duplicate_request':
        print("\n" + "=" * 80)
        print("✅ SUCCESS: Deduplication is working correctly!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ FAILED: Deduplication did not work as expected!")
        print("=" * 80)
    
    print("\n\n3. Third Request - DIFFERENT INPUT (should process normally):")
    print("-" * 80)
    test_input_different = {
        "user": "test@example.com",
        "source": "email",
        "input": "This is a DIFFERENT test message",  # Different input
        "subject": "Test Subject",
        "created_at": datetime.now().isoformat()
    }
    result3 = await process_request_async(test_input_different)
    print(f"\nResult 3 Status: {result3.get('status')}")
    if result3.get('request_id'):
        print(f"Request ID: {result3.get('request_id')}")
        print(f"Request Hash: {result3.get('request_hash')}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    # Note: This test will try to actually process requests
    # You may see errors if OpenAI API keys or other services are not configured
    # The important part is to verify the deduplication logic itself
    
    print("\nNOTE: This test may show errors related to missing API keys or services.")
    print("Focus on the deduplication behavior (skipped duplicate requests).\n")
    
    try:
        asyncio.run(test_deduplication())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nTest error: {e}")
        print("This is expected if services/API keys are not configured.")
        print("The key thing is whether duplicate detection worked before the error.")

