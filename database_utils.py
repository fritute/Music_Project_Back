"""
Utilitários para gerenciamento do banco de dados MongoDB
"""
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

async def init_collections(db: AsyncIOMotorDatabase):
    """
    Inicializa as coleções necessárias com índices apropriados
    """
    try:
        # Lista das coleções necessárias
        required_collections = ['users', 'musics', 'playlists']
        
        # Verificar coleções existentes
        existing_collections = await db.list_collection_names()
        logger.info(f"📚 Coleções existentes: {existing_collections}")
        
        # Criar índices para coleção de usuários
        if 'users' not in existing_collections:
            await db.create_collection('users')
            logger.info("✅ Coleção 'users' criada")
        
        # Índice único para email
        await db.users.create_index("email", unique=True)
        logger.info("✅ Índice único criado para email")
        
        # Criar índices para coleção de músicas
        if 'musics' not in existing_collections:
            await db.create_collection('musics')
            logger.info("✅ Coleção 'musics' criada")
        
        # Índices para busca de músicas
        await db.musics.create_index([
            ("title", "text"), 
            ("artist", "text"), 
            ("genre", "text")
        ])
        await db.musics.create_index("uploadedBy")
        await db.musics.create_index("createdAt")
        logger.info("✅ Índices criados para músicas")
        
        # Criar índices para coleção de playlists
        if 'playlists' not in existing_collections:
            await db.create_collection('playlists')
            logger.info("✅ Coleção 'playlists' criada")
        
        await db.playlists.create_index("userId")
        await db.playlists.create_index("createdAt")
        logger.info("✅ Índices criados para playlists")
        
        logger.info("🎉 Database inicializado com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar coleções: {e}")
        return False

async def check_database_health(db: AsyncIOMotorDatabase) -> dict:
    """
    Verifica a saúde do banco de dados
    """
    try:
        # Contar documentos em cada coleção
        collections_info = {}
        
        collections = ['users', 'musics', 'playlists']
        for collection_name in collections:
            count = await db[collection_name].count_documents({})
            collections_info[collection_name] = count
        
        return {
            "status": "healthy",
            "collections": collections_info,
            "total_documents": sum(collections_info.values())
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }