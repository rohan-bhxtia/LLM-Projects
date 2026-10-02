import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

# now we need to import tools.py
import tools

load_dotenv()

MODEL = "gemini-flash-latest"
STOP_WORDS = {"stop", "exit", "quit"}


# we need to fetch tools from there if they are being used ..
# every variable in tools.py ending with "_tool" is a tool structure,
# and its "name" is the name of the working function in tools.py
tool_structures = [value for name, value in vars(tools).items() if name.endswith("_tool")]
tool_functions = {tool["name"]: getattr(tools, tool["name"]) for tool in tool_structures}


# description is defined there and we need to give gemini the structure. and tell them to use the
# corresponding working function
gemini_tools = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name=tool["name"],
            description=tool["description"],
            parameters_json_schema=tool["parameters"],
        )
        for tool in tool_structures
    ]
)

client = genai.Client(api_key=os.getenv("G_api"))
chat = client.chats.create(
    model=MODEL,
    config=types.GenerateContentConfig(
        tools=[gemini_tools],
        system_instruction=(
            "You are a personal finance assistant. Use the tools for stock prices, "
            "currency conversion and tracking income/expenses. Answer clearly and briefly."
        ),
    ),
)


def run_tool(name, args):
    function = tool_functions.get(name)
    if function is None:
        return {"error": f"Unknown tool {name}"}
    try:
        return function(**args)
    except Exception as e:
        return {"error": str(e)}


# .. and then get back results from there and show us in chat .. chat wont end until user say stop.
print(f"Finance assistant ready. Tools: {', '.join(tool_functions)}. Type 'stop' to end.\n")

while True:
    user_input = input("You: ").strip()
    if not user_input:
        continue
    if user_input.lower() in STOP_WORDS:
        print("Bye!")
        break

    response = chat.send_message(user_input)

    # gemini may ask for one or more tools; run them and send results back until it answers in text
    while response.function_calls:
        results = []
        for call in response.function_calls:
            args = dict(call.args or {})
            print(f"  [using {call.name} with {args}]")
            result = run_tool(call.name, args)
            results.append(types.Part.from_function_response(name=call.name, response={"result": result}))
        response = chat.send_message(results)

    print(f"Gemini: {response.text}\n")
