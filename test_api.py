#!/usr/bin/env python3
"""
Script de teste para verificar se a API está funcionando corretamente
"""

import requests
import json
import time
from pathlib import Path

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_cors(self):
        """Testa configuração de CORS"""
        print("🔍 Testando CORS...")
        
        try:
            # Teste OPTIONS (preflight)
            response = self.session.options(
                f"{self.base_url}/test-cors",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            print(f"   OPTIONS Status: {response.status_code}")
            print(f"   CORS Headers: {dict(response.headers)}")
            
            # Teste GET normal
            response = self.session.get(
                f"{self.base_url}/test-cors",
                headers={"Origin": "http://localhost:3000"}
            )
            
            print(f"   GET Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.json()}")
                print("   ✅ CORS funcionando!")
            else:
                print("   ❌ CORS com problemas!")
                
        except Exception as e:
            print(f"   ❌ Erro ao testar CORS: {e}")
    
    def test_health(self):
        """Testa saúde da API"""
        print("🏥 Testando saúde da API...")
        
        try:
            response = self.session.get(f"{self.base_url}/")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Message: {data.get('message')}")
                print(f"   Database: {data.get('database')}")
                print("   ✅ API funcionando!")
            else:
                print("   ❌ API com problemas!")
                
        except Exception as e:
            print(f"   ❌ Erro ao testar API: {e}")
    
    def test_api_routes(self):
        """Testa rotas da API"""
        print("🚀 Testando rotas da API...")
        
        routes_to_test = [
            "/api/",
            "/api/auth/register",  # POST
            "/api/music",          # GET  
        ]
        
        for route in routes_to_test:
            try:
                url = f"{self.base_url}{route}"
                
                if "register" in route:
                    # POST test with dummy data
                    response = self.session.post(url, json={
                        "name": "Test User",
                        "email": "test@example.com",
                        "password": "testpass123"
                    })
                else:
                    # GET test
                    response = self.session.get(url)
                
                print(f"   {route}: Status {response.status_code}")
                
                if response.status_code not in [404, 422, 401]:  # Códigos esperados para testes sem auth
                    print("   ✅ Rota acessível")
                else:
                    print("   ⚠️  Rota protegida/não implementada (esperado)")
                    
            except Exception as e:
                print(f"   ❌ Erro ao testar {route}: {e}")

def main():
    print("""
🎵 Testador MusicStream API
===========================
    """)
    
    # Verificar se servidor está rodando
    tester = APITester()
    
    print("⏳ Aguardando servidor...")
    time.sleep(2)
    
    # Executar testes
    tester.test_health()
    print()
    tester.test_cors() 
    print()
    tester.test_api_routes()
    
    print("""
🏁 Teste concluído!
Verifique os resultados acima.
    """)

if __name__ == "__main__":
    main()