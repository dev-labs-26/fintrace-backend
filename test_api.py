#!/usr/bin/env python3
"""
API Testing Script for Fintrace Backend
Tests all endpoints to ensure Railway deployment is working correctly
"""

import sys
import requests
import json
from pathlib import Path


def test_health_check(base_url: str) -> bool:
    """Test the health check endpoint"""
    print("\n1. Testing Health Check Endpoint...")
    print(f"   GET {base_url}/health")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("   ✅ Health check passed!")
            return True
        else:
            print(f"   ❌ Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_analyze_endpoint(base_url: str, csv_file: str = "test_transactions.csv") -> bool:
    """Test the analyze endpoint with a CSV file"""
    print("\n2. Testing Analyze Endpoint...")
    print(f"   POST {base_url}/analyze")
    
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"   ⚠️  Test file '{csv_file}' not found. Skipping analyze test.")
        print(f"   Create a test CSV file with columns: transaction_id, sender_id, receiver_id, amount, timestamp")
        return False
    
    try:
        with open(csv_path, 'rb') as f:
            files = {'file': (csv_file, f, 'text/csv')}
            response = requests.post(
                f"{base_url}/analyze",
                files=files,
                timeout=30
            )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Analysis completed successfully!")
            print(f"\n   Results Summary:")
            print(f"   - Total accounts analyzed: {data['summary']['total_accounts_analyzed']}")
            print(f"   - Suspicious accounts: {data['summary']['suspicious_accounts_flagged']}")
            print(f"   - Fraud rings detected: {data['summary']['fraud_rings_detected']}")
            print(f"   - Processing time: {data['summary']['processing_time_seconds']:.3f}s")
            
            if data['suspicious_accounts']:
                print(f"\n   Sample suspicious account:")
                account = data['suspicious_accounts'][0]
                print(f"   - Account ID: {account['account_id']}")
                print(f"   - Suspicion score: {account['suspicion_score']}")
                print(f"   - Patterns: {', '.join(account['detected_patterns'])}")
            
            return True
        else:
            print(f"   ❌ Analysis failed with status {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_docs_endpoint(base_url: str) -> bool:
    """Test that API documentation is accessible"""
    print("\n3. Testing API Documentation...")
    print(f"   GET {base_url}/docs")
    
    try:
        response = requests.get(f"{base_url}/docs", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ API documentation is accessible!")
            print(f"   Visit: {base_url}/docs")
            return True
        else:
            print(f"   ❌ Documentation endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_cors_headers(base_url: str) -> bool:
    """Test CORS headers are properly configured"""
    print("\n4. Testing CORS Configuration...")
    print(f"   OPTIONS {base_url}/analyze")
    
    try:
        # Simulate a preflight request
        headers = {
            'Origin': 'https://example.vercel.app',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type',
        }
        response = requests.options(f"{base_url}/analyze", headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
        }
        
        print(f"   CORS Headers:")
        for key, value in cors_headers.items():
            if value:
                print(f"   - {key}: {value}")
        
        if cors_headers['Access-Control-Allow-Origin']:
            print("   ✅ CORS is configured!")
            return True
        else:
            print("   ⚠️  CORS headers not found (may need to set ALLOWED_ORIGINS)")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all API tests"""
    print("=" * 70)
    print("Fintrace Backend API Test Suite")
    print("=" * 70)
    
    # Get base URL from command line or use default
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        base_url = input("\nEnter your Railway backend URL (or press Enter for localhost): ").strip()
        if not base_url:
            base_url = "http://localhost:8000"
        else:
            base_url = base_url.rstrip('/')
    
    print(f"\nTesting API at: {base_url}")
    print("=" * 70)
    
    # Run tests
    results = {
        'Health Check': test_health_check(base_url),
        'Analyze Endpoint': test_analyze_endpoint(base_url),
        'API Documentation': test_docs_endpoint(base_url),
        'CORS Configuration': test_cors_headers(base_url),
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your API is ready for production!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("1. Set ALLOWED_ORIGINS in Railway to your Vercel domain")
    print("2. Update frontend API_URL to your Railway URL")
    print("3. Test file upload from your frontend")
    print("=" * 70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
