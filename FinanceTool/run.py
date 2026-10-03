import os
import sys

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

import tools


load_dotenv()

MODEL = "gemini-3.6-flash"

MAX_TOOL_ROUNDS = 5


# --------------------------------
# Check API key before starting
# --------------------------------

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

        types.FunctionDeclaration(
            name=tools.show_transactions_tool["name"],
            description=tools.show_transactions_tool["description"],
            parameters_json_schema=tools.show_transactions_tool["parameters"],
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
            "After recording income or expenses, only mention the transaction(s) "
            "just recorded and the remaining balance. "
            "List all transactions only when the user asks for them. "
            "Answer clearly and briefly."
        ),
    ),
)


# --------------------------------
# Run the actual Python tool
# --------------------------------

def run_tool(name, args):
    try:
        if name == "stock_price":
            return tools.stock_price(**args)

        if name == "currency_conversion":
            return tools.currency_conversion(**args)

        if name == "expense_calculator":
            return tools.expense_calculator(**args)

        if name == "show_transactions":
            return tools.show_transactions()

        return {"error": f"Unknown tool: {name}"}

    except TypeError as e:
        return {"error": f"Wrong arguments for {name}: {e}"}

    except Exception as e:
        return {"error": f"{name} failed: {e}"}


# --------------------------------
# Main chat loop
# --------------------------------

while True:
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

    try:
        response = chat.send_message(user_input)

        # --------------------------------
        # Handle tool calls
        # --------------------------------

        tool_rounds = 0

        while response.function_calls:
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

            response = chat.send_message(results)

        else:
            # --------------------------------
            # Print Gemini's final answer
            # --------------------------------

            if response.text:
                print(f"BOT: {response.text}\n")
            else:
                print("BOT: (no answer, please try again)\n")

    except KeyboardInterrupt:
        print("\nBye!")
        break

    except errors.ClientError as e:
        print(f"BOT error (check API key / model name / limits): {e}\n")

    except errors.ServerError as e:
        print(f"BOT server error, please try again in a moment: {e}\n")

    except Exception as e:
        print(f"Something went wrong: {e}\n")
