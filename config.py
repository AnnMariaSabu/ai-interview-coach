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
# 🎨 A bit more creativity when WRITING questions, so repeat interviews feel new
QUESTION_TEMPERATURE = 0.7

# 🗺️ Skill matching: similarity above this = the skill matches
# Chosen from the experiment in explore_similarity.py (matches >= 0.65, non-matches <= 0.57)
MATCH_THRESHOLD = 0.61

# 📊 Match score: points for each matched skill
REQUIRED_WEIGHT = 2
NICE_TO_HAVE_WEIGHT = 1

# 🎤 Interview rules
MIN_QUESTIONS = 8
MAX_QUESTIONS = 10
MAX_FOLLOW_UPS = 1

# 🔁 Repeat interviews: how many earlier questions the AI is told not to repeat
EARLIER_QUESTIONS_TO_AVOID = 10

# ⚡ Feedback at the end: follow-ups still happen, but scoring waits until the interview is finished
FEEDBACK_AT_END = True

# 📊 Scoring rubric (each criterion is scored 1 to 5)
SCORE_MIN = 1
SCORE_MAX = 5
RUBRIC = ["Relevance", "Structure", "Specifics", "Clarity", "Technical accuracy"]

# 📁 Where files are stored
DATA_DIR = "data"
DB_PATH = "data/interviews.db"