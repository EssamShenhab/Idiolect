from zenml import step


@step
def greet(name: str) -> str:
    message = f"Hello {name}! This is version 2."
    print(message)
    return message