from .utils import get_current_time

def greet(name: str) -> str:
    """
    Greets the given name.
    """
    return f"Hello, {name}!"

def main():
    """
    Main function to run the application.
    """
    current_time = get_current_time()
    print(f"Welcome to Your Awesome Project! The current time is {current_time}.")
    print(greet("Developer"))

if __name__ == "__main__":
    main()
