import time
import functools

def timed(func):
    """Decorator to time function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"✓ {func.__name__} completed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper