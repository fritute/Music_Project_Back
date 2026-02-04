#!/usr/bin/env python3
"""
Script para inicializar o servidor MusicStream API
Configurações otimizadas para desenvolvimento e produção
"""

import uvicorn
import os
from pathlib import Path

def main():
    """Inicializar o servidor com configurações otimizadas"""
    
    # Garantir que as pastas de upload existam
    upload_dirs = [
        Path("uploads/music"),
        Path("uploads/covers")
    ]
    
    for dir_path in upload_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Diretório criado/verificado: {dir_path}")
    
    # Configurações do servidor
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    print(f"""
🎵 Iniciando MusicStream API...
   Host: {host}
   Porta: {port}
   Modo: {'Desenvolvimento' if reload else 'Produção'}
   Reload: {'Ativado' if reload else 'Desativado'}
   
📁 Endpoints disponíveis:
   - Docs: http://{host}:{port}/docs
   - API: http://{host}:{port}/api
   - Health: http://{host}:{port}/test-cors
    """)
    
    try:
        uvicorn.run(
            "server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True,
            use_colors=True,
            reload_dirs=["./"] if reload else None
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")

if __name__ == "__main__":
    main()