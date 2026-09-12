"""
Private Agent Configuration
Loads environment variables for local execution inside the company perimeter.
"""
import os
from packages.shared.constants import DataEgressMode

class AgentConfig:
    CONTROL_PLANE_URL = os.environ.get("CONTROL_PLANE_URL", "http://localhost:8000")
    AGENT_ID = os.environ.get("AGENT_ID", "agt_local_001")
    AGENT_TOKEN = os.environ.get("AGENT_TOKEN", "sopq_agt_local_secret")
    TENANT_ID = os.environ.get("TENANT_ID", "ten_acme_default")
    VERSION = "1.0.4"

    STORAGE_PATH = os.environ.get("STORAGE_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage_data"))
    DB_PATH = os.environ.get("AGENT_DB_PATH", os.path.join(STORAGE_PATH, "private_agent.db"))

    DATA_EGRESS_MODE = DataEgressMode(os.environ.get("DATA_EGRESS_MODE", "PRIVATE_ONLY"))
    LLM_MODE = os.environ.get("LLM_MODE", "LOCAL")  # LOCAL, OLLAMA, CUSTOMER, REMOTE
    LOCAL_LLM_BASE_URL = os.environ.get("LOCAL_LLM_BASE_URL", "http://localhost:11434")
    LOCAL_LLM_MODEL = os.environ.get("LOCAL_LLM_MODEL", "llama3.2")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "bge-small-en-v1.5")

    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50 MB
    MAX_AUDIO_DURATION = int(os.environ.get("MAX_AUDIO_DURATION", 14400))   # 4 hours in seconds

    # Ensure storage directories exist safely
    os.makedirs(STORAGE_PATH, exist_ok=True)
    os.makedirs(os.path.join(STORAGE_PATH, "documents"), exist_ok=True)
    os.makedirs(os.path.join(STORAGE_PATH, "meetings"), exist_ok=True)

config = AgentConfig()
