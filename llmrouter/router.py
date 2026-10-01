from providers import gemini, llama, mistral


def route(category: str, prompt: str) -> str:
    providers = {
        "coding": gemini.generate,
        "research": gemini.generate,
        "writing": mistral.generate,
        "general": llama.generate,
    }

    provider = providers.get(category)

    if not provider:
        return "Unknown category"

    return provider(prompt)
