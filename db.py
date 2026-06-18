import os
from dotenv import load_dotenv
from pymongo import MongoClient
MONGO_URI="mongodb+srv://anas:1111@cluster0.pqdldhh.mongodb.net/?appName=Cluster0"

DB_NAME="powerbidata"
PRED_COLLECTION="powerbidata"
# Load .env from the SAME folder as db.py (works with uvicorn reload too)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MONGO_URI = MONGO_URI
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not found. Check .env in project folder")

client = MongoClient(MONGO_URI)

DB_NAME = DB_NAME
COL_NAME = PRED_COLLECTION

db = client[DB_NAME]
predictions_col = db[COL_NAME]
