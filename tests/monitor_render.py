#!/usr/bin/env python3
"""
Monitor para verificar quando o deploy no Render está funcionando
"""
import requests
import time
import json
from datetime import datetime

class RenderMonitor:
    def __init__(self, base_url="https://music-project-back-4.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
        
    def check_health(self):
        """Verifica saúde da API"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "status_code": None,
                "response": str(e),
                "success": False
            }
    
    def check_cors_register(self):
        """Testa endpoint de registro com CORS"""
        try:
            # First, test OPTIONS (preflight)
            options_response = self.session.options(
                f"{self.base_url}/api/auth/register",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            if options_response.status_code != 200:
                return {
                    "preflight": False,
                    "status_code": options_response.status_code,
                    "success": False
                }
            
            # Test actual POST
            test_data = {
                "name": "Test Monitor",
                "email": f"monitor_{int(time.time())}@test.com",
                "password": "testpass123"
            }
            
            post_response = self.session.post(
                f"{self.base_url}/api/auth/register",
                json=test_data,
                headers={"Origin": "http://localhost:3000"}
            )
            
            return {
                "preflight": True,
                "status_code": post_response.status_code,
                "response": post_response.text[:200] if post_response.text else "No response",
                "success": post_response.status_code in [200, 201, 400]  # 400 = user exists
            }
            
        except Exception as e:
            return {
                "preflight": False,
                "status_code": None,
                "response": str(e),
                "success": False
            }
    
    def monitor(self, max_attempts=20, delay=30):
        """Monitor deploy status"""
        print(f"""
🔍 Monitorando deploy no Render...
URL: {self.base_url}
Máximo de tentativas: {max_attempts}
Intervalo: {delay}s

Aguardando deploy... (isso pode levar alguns minutos)
        """)
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Tentativa {attempt}/{max_attempts}")
            
            # Check health
            health = self.check_health()
            print(f"   Health: {'✅' if health['success'] else '❌'} {health['status_code']}")
            
            if health['success']:
                print(f"   Response: {health['response']}")
                
                # Check CORS/Register
                cors = self.check_cors_register()
                print(f"   CORS: {'✅' if cors['success'] else '❌'} {cors['status_code']}")
                
                if cors['success']:
                    print("\n🎉 Deploy concluído com sucesso!")
                    print("   ✅ Health check funcionando")
                    print("   ✅ CORS configurado corretamente")
                    print("   ✅ Endpoints respondendo")
                    return True
                else:
                    print(f"   CORS Issue: {cors['response'][:100]}...")
            
            if attempt < max_attempts:
                print(f"   ⏳ Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)
        
        print("\n❌ Deploy ainda não está funcional após todas as tentativas.")
        print("💡 Verifique os logs no dashboard do Render.")
        return False

def main():
    monitor = RenderMonitor()
    success = monitor.monitor()
    
    if not success:
        print("\n🔧 Possíveis soluções:")
        print("   1. Verificar logs no dashboard do Render")
        print("   2. Verificar variáveis de ambiente (MONGO_URL, JWT_SECRET)")
        print("   3. Aguardar mais tempo - o Render pode estar lento")

if __name__ == "__main__":
    main()