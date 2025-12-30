import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4"
    
    # File paths
    PROJECTS_JSON = "data/cleaned_products.json"
    PROMPTS_DIR = "prompts"
    CHAT_HISTORY_FILE = "chat_history/all_projects_history.json"
    
    # BA Agent settings
    MAX_HISTORY_PER_PROJECT = 50
    TEMPERATURE = 0.2
    DEFAULT_RESPONSE_STYLE = "detailed"
    DEFAULT_SCOPE = "specific"
    DEFAULT_STRICT_MODE = False

config = Config()