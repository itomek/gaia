from gaia.logger import get_logger

logger = get_logger(__name__)

# Optional imports for other agents
try:
    from gaia.agents.Llm.app import LlmApp as llm
except ImportError:
    logger.debug("Llm agent not available")
    llm = None

try:
    from gaia.agents.chat.app import ChatApp as chat
except ImportError:
    logger.debug("Chat agent not available")
    chat = None
