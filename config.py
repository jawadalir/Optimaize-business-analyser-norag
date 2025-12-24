import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o"  # You can change to gpt-3.5-turbo if needed
    
    # File paths
    PROJECTS_JSON = "data/cleaned_products.json"
    PROMPTS_DIR = "prompts"
    CHAT_HISTORY_FILE = "chat_history/all_projects_history.json"
    
    # BA Agent settings
    MAX_HISTORY_PER_PROJECT = 50  # Keep last 50 messages per project
    TEMPERATURE = 0.3  # Lower for more consistent BA analysis
    DEFAULT_RESPONSE_STYLE = "detailed"  # "simple" or "detailed"
    DEFAULT_SCOPE = "specific"  # "specific" or "general"
    
config = Config()