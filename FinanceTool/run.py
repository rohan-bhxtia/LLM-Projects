import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

import tools


load_dotenv()

MODEL = "gemini-3.5-flash"

# Max times Gemini can ask for tools for one message (stops endless tool loops)
MAX_TOOL_ROUNDS = 5


# --------------------------------
# Check API key before starting
# --------------------------------

# If the Gemini key is missing, stop now with a clear message
# instead of failing later with a confusing error
api_key = os.getenv("G_api")
if not api_key:
    sys.exit("Error: G_api is missing in .env. Add your Gemini API key and try again.")


# --------------------------------
# Give Gemini our tool definitions
# --------------------------------

gemini_tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name=tools.stock_price_tool["name"],
            description=tools.stock_price_tool["description"],
            parameters_json_schema=tools.stock_price_tool["parameters"],
        ),

        types.FunctionDeclaration(
            name=tools.currency_conversion_tool["name"],
            description=tools.currency_conversion_tool["description"],
            parameters_json_schema=tools.currency_conversion_tool["parameters"],
        ),

        types.FunctionDeclaration(
            name=tools.expense_calculator_tool["name"],
            description=tools.expense_calculator_tool["description"],
            parameters_json_schema=tools.expense_calculator_tool["parameters"],
        ),
    ]
)


# --------------------------------
# Create Gemini client
# --------------------------------

client = genai.Client(
    api_key=api_key
)


# --------------------------------
# Create chat
# --------------------------------

chat = client.chats.create(
    model=MODEL,
    config=types.GenerateContentConfig(
        tools=[gemini_tools],
        system_instruction=(
            "Your name is BOT, a personal finance assistant. "
            "Use the available tools when necessary. "
            "Answer clearly and briefly."
        ),
    ),
)


# --------------------------------
# Run the actual Python tool
# --------------------------------

def run_tool(name, args):

    # If a tool crashes (no internet, API down, wrong arguments from Gemini),
    # return the error to Gemini instead of crashing the whole chat.
    # Gemini can then explain the problem to the user.
    try:

        if name == "stock_price":
            return tools.stock_price(**args)

        if name == "currency_conversion":
            return tools.currency_conversion(**args)

        if name == "expense_calculator":
            return tools.expense_calculator(**args)

        return {"error": f"Unknown tool: {name}"}

    except TypeError as e:
        # Gemini sent missing or extra arguments for this tool
        return {"error": f"Wrong arguments for {name}: {e}"}

    except Exception as e:
        # Any other problem inside the tool (network error, bad API response, etc.)
        return {"error": f"{name} failed: {e}"}


# --------------------------------
# Main chat loop
# --------------------------------

while True:

    # Ctrl+C or Ctrl+D ends the chat cleanly instead of showing an error trace
    try:
        user_input = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nBye!")
        break

    if not user_input:
        continue

    if user_input.lower() in {"stop", "exit", "quit"}:
        print("Bye!")
        break

    # Gemini errors (no internet, wrong key, wrong model name, rate limit)
    # should not end the chat. Show the error and let the user try again.
    try:

        # Send user message to Gemini
        response = chat.send_message(user_input)


        # --------------------------------
        # Handle tool calls
        # --------------------------------

        tool_rounds = 0

        while response.function_calls:

            # Stop if Gemini keeps asking for tools again and again
            tool_rounds += 1
            if tool_rounds > MAX_TOOL_ROUNDS:
                print("BOT: Sorry, I couldn't finish this request. Please try asking differently.\n")
                break

            results = []

            for call in response.function_calls:

                args = dict(call.args or {})

                print(f"[Using {call.name}: {args}]")

                result = run_tool(call.name, args)

                results.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response={"result": result},
                    )
                )

            # Send tool results back to Gemini
            response = chat.send_message(results)

        else:
            # this "else" belongs to the while loop above: it runs only when Gemini
            # stopped asking for tools, and is skipped if we hit "break" (too many rounds)

            # --------------------------------
            # Print Gemini's final answer
            # --------------------------------

            # Gemini can sometimes reply with no text; don't print "None"
            if response.text:
                print(f"BOT: {response.text}\n")
            else:
                print("BOT: (no answer, please try again)\n")

    except KeyboardInterrupt:
        # Ctrl+C while waiting for Gemini or a tool. KeyboardInterrupt is not an
        # "Exception" in Python, so "except Exception" below does not catch it.
        print("\nBye!")
        break

    except errors.ClientError as e:
        # Problem with our request: wrong API key, wrong model name, rate limit (429)
        print(f"BOT error (check API key / model name / limits): {e}\n")

    except errors.ServerError as e:
        # Problem on Google's side, usually temporary
        print(f"BOT server error, please try again in a moment: {e}\n")

    except Exception as e:
        # Anything else, e.g. no internet connection
        print(f"Something went wrong: {e}\n")
