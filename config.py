"""
Settings for the AI Interview Coach.
Change values here, not inside the rest of the code.
"""

# 🤖 AI models (they run locally with Ollama)
CHAT_MODEL = "llama3.2"           # thinks and talks
EMBED_MODEL = "nomic-embed-text"  # turns meaning into numbers

# 🔌 Where Ollama runs on your laptop
OLLAMA_URL = "http://localhost:11434"

# 🎲 AI creativity: 0 = gives the same answer every time (good for fair scoring)
TEMPERATURE = 0

# 🎤 Interview rules
MIN_QUESTIONS = 8
MAX_QUESTIONS = 10
MAX_FOLLOW_UPS = 2

# 📊 Scoring rubric (each criterion is scored 1 to 5)
SCORE_MIN = 1
SCORE_MAX = 5
RUBRIC = ["Relevance", "Structure", "Specifics", "Clarity", "Technical accuracy"]

# 📁 Where files are stored
DATA_DIR = "data"
DB_PATH = "data/interviews.db"