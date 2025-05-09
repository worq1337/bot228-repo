import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the current directory
load_dotenv()

# Retrieve the token and base_url from the environment
TOKEN = os.getenv("TOKEN")
BASE_URL = os.getenv("BASE_URL")
DATABASE_URL = os.getenv("DATABASE_URL")
WEB_SERVER_HOST = os.getenv("WEB_SERVER_HOST")
WEB_SERVER_PORT = int(os.getenv("WEB_SERVER_PORT"))  # Convert to integer
MAIN_BOT_PATH = os.getenv("MAIN_BOT_PATH")
OTHER_BOTS_PATH = os.getenv("OTHER_BOTS_PATH")
OTHER_BOTS_URL = f"{BASE_URL}{OTHER_BOTS_PATH}"
ADMIN = [2003019116,61444003,6973491393,7218613643,6438938979]

if TOKEN is None:
    raise ValueError("TOKEN is not set in the .env file.")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set in the .env file.")

if BASE_URL is None:
    raise ValueError("BASE_URL is not set in the .env file.")

if WEB_SERVER_HOST is None:
    raise ValueError("WEB_SERVER_HOST is not set in the .env file.")

if WEB_SERVER_PORT is None:
    raise ValueError("WEB_SERVER_PORT is not set in the .env file.")

if MAIN_BOT_PATH is None:
    raise ValueError("MAIN_BOT_PATH is not set in the .env file.")

if OTHER_BOTS_PATH is None:
    raise ValueError("OTHER_BOTS_PATH is not set in the .env file.")

if ADMIN is None:
    raise ValueError("ADMIN is not set in the .env file.")

if OTHER_BOTS_PATH is None:
    raise ValueError("OTHER_BOTS_PATH is not set in the .env file.")

if ADMIN is None:
    raise ValueError("ADMIN is not set in the .env file.")
