import os

from dotenv import load_dotenv
from google import genai
from google.genai import types


load_dotenv()

client = genai.Client(
    api_key=os.getenv("Gemini_Api")
)


def generate(prompt: str) -> str:

    response = client.models.generate_content_stream(
        
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            system_instruction=(
                "Answer the user's question clearly but with a little sarcastic and aggresion."
            ),
        ),
    )
    for chunk in response:
        print(chunk.text, end="", flush=True)


if __name__ == "__main__":
    prompt = input("Enter your prompt: ")
    generate(prompt)