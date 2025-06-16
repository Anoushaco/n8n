import datetime

def get_current_time() -> str:
    """
    Returns the current time as a formatted string.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def simple_utility_function() -> str:
    """
    A simple utility function.
    """
    return "This is a utility function."
