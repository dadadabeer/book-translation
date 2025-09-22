# src/client.py
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("SEALION_API_KEY"),
    base_url="https://api.sea-lion.ai/v1"
)

def get_client():
    return client
