import os

from dotenv import load_dotenv
from mistralai.client import Mistral


load_dotenv()

client = Mistral(api_key=os.getenv("Mistral_API"))


def generate(prompt: str) -> str:
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content
