#!/usr/bin/env python3
"""
Script para testar conexão com MongoDB Atlas
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def test_atlas_connection():
    """Testa conexão com MongoDB Atlas"""
    
    mongo_url = os.getenv('MONGO_URL')
    db_name = os.getenv('DB_NAME', 'musicstream')
    
    if not mongo_url:
        print("❌ MONGO_URL não encontrada no arquivo .env")
        return
    
    print(f"🔗 Testando conexão Atlas...")
    print(f"   URL: {mongo_url[:50]}...")
    print(f"   Database: {db_name}")
    print()
    
    try:
        # Create client with ServerApi
        client = AsyncIOMotorClient(
            mongo_url,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=15000,
            socketTimeoutMS=15000,
            server_api=ServerApi('1')
        )
        
        print("⏳ Conectando...")
        
        # Test connection
        result = await client.admin.command('ping')
        print("✅ Ping successful!")
        
        # Get database
        db = client[db_name]
        
        # Test database operations
        server_info = await client.server_info()
        print(f"📊 MongoDB Version: {server_info.get('version', 'unknown')}")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"📚 Coleções: {collections if collections else 'Nenhuma'}")
        
        # Test insert/read
        test_collection = db.test_connection
        
        # Insert test document
        test_doc = {"message": "test", "timestamp": "2026-02-04"}
        result = await test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted: {result.inserted_id}")
        
        # Read test document
        doc = await test_collection.find_one({"_id": result.inserted_id})
        print(f"📖 Test document read: {doc['message']}")
        
        # Clean up test document
        await test_collection.delete_one({"_id": result.inserted_id})
        print("🗑️ Test document cleaned up")
        
        client.close()
        print()
        print("🎉 Conexão Atlas funcionando perfeitamente!")
        
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")
        print()
        print("💡 Possíveis soluções:")
        print("   1. Verifique suas credenciais no MongoDB Atlas")
        print("   2. Verifique se seu IP está na whitelist")
        print("   3. Verifique sua conexão de internet")
        print("   4. Verifique se o cluster está ativo")

if __name__ == "__main__":
    asyncio.run(test_atlas_connection())