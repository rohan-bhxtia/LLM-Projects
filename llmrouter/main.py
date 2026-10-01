from classifier import classify
from router import route


while True:
    user_prompt = input("Enter your prompt: ")

    if user_prompt == "stop()":
        break

    category_from_classifier = classify(user_prompt)
    response = route(category_from_classifier, user_prompt)

    print(response)
