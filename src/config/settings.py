import os
from typing import List

# Simple Agno-style configuration
class Settings:
    def __init__(self):
        # API Keys
        self.openrouter_api_key: str = os.getenv(
            "OPENROUTER_API_KEY",
            "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"
        )
        
        # Tavily API Key for web search (optional)
        self.tavily_api_key: str = os.getenv("TAVILY_API_KEY", "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")
        
        # Database
        self.agent_storage_db: str = os.getenv("AGENT_STORAGE_DB", "tmp/agents.db")
        
        # MCP Server
        self.mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://localhost:8001/sse")
        
        # Logging
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        
        # CORS
        cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:4321")
        self.cors_origins: List[str] = [origin.strip() for origin in cors_origins_str.split(",")]
        
        # Model Configuration
        self.default_model_id: str = "google/gemini-2.5-flash-preview-05-20:thinking"
        self.openrouter_base_url: str = "https://openrouter.ai/api/v1"
        
        # Agent Configuration
        self.num_history_responses: int = 3


# Global settings instance
settings = Settings() 