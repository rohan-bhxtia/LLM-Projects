import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

api_key = os.getenv("Gemini_Api")
client = genai.Client(api_key=api_key)

def classify(prompt):


    classification_prompt = f"""
    Classify this prompt into one of these categories: coding, research, writing, general.
    Return only the category name.

    Prompt: {prompt}
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=classification_prompt,
        config=types.GenerateContentConfig(
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    category = response.text.strip().lower()
    return category
