import os
from enum import Enum

import requests
from dotenv import load_dotenv

load_dotenv()


# # define structure of stock price tool
# # name it stock price tool
# # define the python structure
stock_price_tool = {
    "name": "stock_price",
    "description": "Get the latest price of a stock by its ticker symbol, e.g. AAPL.",
    "parameters": {
        "type": "object",
        "properties": {
            "stock_name": {"type": "string", 
                           "description": "Ticker symbol of the stock, e.g. AAPL"},
        },
        "required": ["stock_name"],
    },
}

# # now the actual tool with fucntion name stock_price
# # having arguments as stock name that it'll call
# # we have api stored in .env for stock price
def stock_price(stock_name):
    api_key = os.getenv("Stock_api")

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TIME_SERIES_INTRADAY"
        f"&symbol={stock_name.upper()}"
        f"&interval=5min"
        f"&apikey={api_key}"
    )

    response = requests.get(url, timeout=10)     # ← unchanged
    data = response.json()                       # ← unchanged

    prices = data.get("Time Series (5min)")      # ← new: take the price list
    if not prices:
        return {"error": data}                   # wrong symbol, bad key or rate limit

    latest_time = max(prices)                    # newest timestamp
    return {
        "stock": stock_name.upper(),
        "time": latest_time,
        "price": float(prices[latest_time]["4. close"]),
    }


# # same do with currency conversion tool
currency_conversion_tool = {
    "name": "currency_conversion",
    "description": "Convert an amount from one currency to another, e.g. 100 USD to INR.",
    "parameters": {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Amount to convert"},
            "from_currency": {"type": "string", "description": "Currency code to convert from, e.g. USD"},
            "to_currency": {"type": "string", "description": "Currency code to convert to, e.g. INR"},
        },
        "required": ["amount", "from_currency", "to_currency"],
    },
}

def currency_conversion(amount, from_currency, to_currency):
    api_key = os.getenv("currency_api")
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{from_currency}"

    response = requests.get(url, timeout=10)
    data = response.json()

    if data.get("result") != "success":
        return {"error": data.get("error-type", "conversion failed")}

    rates = data["conversion_rates"]  # rates from from_currency to every other currency
    if to_currency not in rates:
        return {"error": f"Unknown currency {to_currency}"}

    rate = rates[to_currency]
    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": rate,
        "converted_amount": round(amount * rate, 2),
    }


# # for expense calculator tool.. we will code .. no api required .. where we'll tell what to add
# #     in expenses and from where money came .. so that it can add or subtract
# # basic usage
class IncomeSource(Enum):
    SALARY = "salary"
    FREELANCE = "freelance"
    BUSINESS = "business"
    INVESTMENT = "investment"
    GIFT = "gift"
    OTHER = "other"


class ExpenseCategory(Enum):
    FOOD = "food"
    RENT = "rent"
    TRAVEL = "travel"
    SHOPPING = "shopping"
    BILLS = "bills"
    HEALTH = "health"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    OTHER = "other"


INCOME_SOURCES = [source.value for source in IncomeSource]
EXPENSE_CATEGORIES = [category.value for category in ExpenseCategory]


expense_calculator_tool = {
    "name": "expense_calculator",
    "description": "Add money (income, with where it came from) or subtract money (expense, with what it was spent on) and return the current balance.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["income", "expense"], "description": "income adds money, expense subtracts money"},
            "amount": {"type": "number", "description": "Amount of money"},
            "category": {
                "type": "string",
                "enum": sorted(set(INCOME_SOURCES + EXPENSE_CATEGORIES)),
                "description": f"For income, where money came from: {', '.join(INCOME_SOURCES)}. "
                               f"For expense, what it was spent on: {', '.join(EXPENSE_CATEGORIES)}",
            },
            "description": {"type": "string", "description": "Extra details, e.g. 'Dominos pizza' or 'October salary'"},
        },
        "required": ["action", "amount", "category"],
    },
}

transactions = []

def expense_calculator(action, amount, category, description=""):
    if action == "income" and category not in INCOME_SOURCES:
        return {"error": f"income category must be one of {INCOME_SOURCES}"}
    if action == "expense" and category not in EXPENSE_CATEGORIES:
        return {"error": f"expense category must be one of {EXPENSE_CATEGORIES}"}

    if action == "expense":
        amount = -amount
    transactions.append({"action": action, "amount": amount, "category": category, "description": description})
    balance = sum(t["amount"] for t in transactions)
    return {"transactions": transactions, "balance": balance}

# # just define these things ... nothing else we'll just make toools here and we'll run the final code from somewhere else
