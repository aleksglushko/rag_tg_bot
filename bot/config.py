import os
from dotenv import load_dotenv
load_dotenv(override=True)

ENV = os.getenv("ENV", "dev")

MONGODB_PATH=os.getenv("MONGODB_PATH")
MONGODB_PORT=os.getenv("MONGODB_PORT")
MONGO_EXPRESS_PORT=os.getenv("MONGO_EXPRESS_PORT")
MONGO_EXPRESS_USERNAME=os.getenv("MONGO_EXPRESS_USERNAME")
MONGO_EXPRESS_PASSWORD=os.getenv("MONGO_EXPRESS_PASSWORD")

openai_api_key = os.getenv("OPENAI_API_KEY")
telegram_token= os.getenv("TELEGRAM_TOKEN")
mongodb_uri = f"mongodb://localhost:{MONGODB_PORT}"