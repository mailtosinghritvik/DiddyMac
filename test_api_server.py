"""Test script for the Bedrock AgentCore API server"""
import requests
import json
import time

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_status():
    """Test status endpoint"""
    print("Testing /status endpoint...")
    response = requests.get(f"{API_URL}/status")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_invoke():
    """Test invoke endpoint"""
    print("Testing /invoke endpoint...")
    response = requests.post(
        f"{API_URL}/invoke",
        json={"inputText": "Hello, this is a test message"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_webhook():
    """Test webhook endpoint"""
    print("Testing /webhook endpoint...")
    response = requests.post(
        f"{API_URL}/webhook",
        json={"message": "Hello from webhook"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def main():
    """Run all tests"""
    print("=" * 70)
    print("Bedrock AgentCore API Server Tests")
    print("=" * 70)
    print()
    print(f"API URL: {API_URL}")
    print("Make sure the server is running: python bedrock_api_server.py")
    print()
    
    try:
        test_health()
        test_status()
        test_invoke()
        test_webhook()
        
        print("=" * 70)
        print("✓ All tests completed!")
        print("=" * 70)
    except requests.exceptions.ConnectionError:
        print("✗ ERROR: Cannot connect to API server")
        print("Make sure the server is running:")
        print("  python bedrock_api_server.py")
    except Exception as e:
        print(f"✗ ERROR: {e}")

if __name__ == "__main__":
    main()

