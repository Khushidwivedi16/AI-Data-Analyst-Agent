import os
from dotenv import load_dotenv

load_dotenv()


def _get_api_key():
    key = os.getenv("GROQ_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GROQ_API_KEY")
    except Exception:
        return None


GROQ_API_KEY = _get_api_key()
MODEL_NAME = "openai/gpt-oss-20b"
RUNTIME_DB_DIR = "runtime_db"
TABLE_NAME = "data"
DATASETS_DIR = "datasets"
MAX_RETRIES = 1