#!/usr/bin/env python3
"""
Script para testar a API deployada no Render
"""
import requests
import json

class RenderAPITester:
    def __init__(self, base_url="https://music-project-back-4.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Add CORS headers to all requests
        self.session.headers.update({
            "Content-Type": "application/json",
            "Origin": "http://localhost:3000"
        })
        
    def test_cors_preflight(self):
        """Test CORS preflight request"""
        print("🔍 Testing CORS Preflight...")
        
        try:
            response = self.session.options(
                f"{self.base_url}/api/auth/register",
                headers={
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type, Authorization"
                }
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            # Check CORS headers
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("access-control-allow-origin"),
                "Access-Control-Allow-Methods": response.headers.get("access-control-allow-methods"),
                "Access-Control-Allow-Headers": response.headers.get("access-control-allow-headers"),
            }
            
            print(f"   CORS Headers: {cors_headers}")
            
            if response.status_code == 200:
                print("   ✅ Preflight successful!")
            else:
                print("   ❌ Preflight failed!")
                
        except Exception as e:
            print(f"   ❌ Error testing preflight: {e}")
    
    def test_api_health(self):
        """Test API health endpoint"""
        print("🏥 Testing API Health...")
        
        try:
            response = self.session.get(f"{self.base_url}/test-cors")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Message: {data.get('message')}")
                print("   ✅ API is healthy!")
            else:
                print(f"   ❌ API health check failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error testing API health: {e}")
    
    def test_register_endpoint(self):
        """Test register endpoint with actual request"""
        print("📝 Testing Register Endpoint...")
        
        try:
            test_user = {
                "name": "Test User",
                "email": f"test_{hash('test')}@example.com",
                "password": "testpass123"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_user
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                print("   ✅ Register endpoint working!")
                data = response.json()
                print(f"   Access token received: {data.get('access_token')[:20]}...")
            elif response.status_code == 400:
                print("   ⚠️ User already exists (expected)")
            else:
                print(f"   ❌ Register failed: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error testing register: {e}")

def main():
    print("""
🚀 Testador da API no Render
=============================
URL: https://music-project-back-4.onrender.com
    """)
    
    tester = RenderAPITester()
    
    # Execute tests
    tester.test_api_health()
    print()
    tester.test_cors_preflight()
    print()
    tester.test_register_endpoint()
    
    print("""
🏁 Teste concluído!
Se todos os testes passaram, o CORS está funcionando corretamente.
    """)

if __name__ == "__main__":
    main()