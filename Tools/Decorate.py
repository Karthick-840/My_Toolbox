import time
from functools import wraps
from typing import Callable, Any
from time import sleep


"""
Dunder methods to find usecase for

equlairt dunder methids  def __eg (self,other:Self) -> bool:
"""

def connect() -> None:
    time.sleep(1)
    raise Exception()

def retry(retries: int = 3, delay: float = 1) -> Callable:
    """
    Attempt to call a function, if it fails, try again with a specified delay.

    :param retries: The max amount of retries you want for the function call
    :param delay: The delay (in seconds) between each function retry
    :return:
    """

    # Don't let the user use this decorator if they are high
    if retries < 1 or delay <= 0:
        raise ValueError('Are you high, mate?')

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for i in range(1, retries + 1):  # 1 to retries + 1 since upper bound is exclusive

                try:
                    print(f'Running ({i}): {func.__name__}()')
                    return func(*args, **kwargs)
                except Exception as e:
                    # Break out of the loop if the max amount of retries is exceeded
                    if i == retries:
                        print(f'Error: {repr(e)}.')
                        print(f'"{func.__name__}()" failed after {retries} retries.')
                        break
                    else:
                        print(f'Error: {repr(e)} -> Retrying...')
                        sleep(delay)  # Add a delay before running the next iteration

        return wrapper

    return decorator


@retry(retries=3, delay=1)
def connect() -> None:
    time.sleep(1)
    raise Exception('Could not connect to internet...')


def main() -> None:
    connect()


if __name__ == '__main__':
    main()
    
    
import time
from functools import cache


@cache
def count_vowels(text: str) -> int:
    """
    A function that counts all the vowels in a given string.

    :param text: The string to analyse
    :return: The amount of vowels as an integer
    """
    vowel_count: int = 0

    # Pretend it's an expensive operation
    print(f'Bot: Counting vowels in: "{text}"...')
    time.sleep(2)

    # Count those damn vowels
    for letter in text:
        if letter in 'aeiouAEIOU':
            vowel_count += 1

    return vowel_count


def main() -> None:
    while True:
        user_input: str = input('You: ')

        if user_input == '!info':
            print(f'Bot: {count_vowels.cache_info()}')
        elif user_input == '!clear':
            print('Bot: Cache cleared!')
            count_vowels.cache_clear()
        else:
            print(f'Bot: "{user_input}" contains {count_vowels(user_input)} vowels.')


if __name__ == '__main__':
    main()
    

import time
from time import perf_counter, sleep
from functools import wraps
from typing import Callable, Any


def get_time(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:

        # Note that timing your code once isn't the most reliable option
        # for timing your code. Look into the timeit module for more accurate
        # timing.
        start_time: float = perf_counter()
        result: Any = func(*args, **kwargs)
        end_time: float = perf_counter()

        print(f'"{func.__name__}()" took {end_time - start_time:.3f} seconds to execute')
        return result

    return wrapper


# Sample function 1
@get_time
def connect() -> None:
    print('Connecting...')
    sleep(2)
    print('Connected!')


# Sample function 2
@get_time
def fifty_million_loops() -> None:
    fifty_million: int = int(5e7)

    print('Looping...')
    for _ in range(fifty_million):
        pass

    print('Done looping!')


def main() -> None:
    fifty_million_loops()
    connect()


if __name__ == '__main__':
    main()
    
# XXX
# XXX TALK ABOUT PEP 702
# XXX https://peps.python.org/pep-0702
# XXX

from deprecated import deprecated


@deprecated("Adding ain't cool no more", version="1.0.0")
def add(x: int, y: int) -> int:
    return x + y


if __name__ == "__main__":
    print(add(5, 7))
    
import atexit


@atexit.register
def exit_handler() -> None:
    print("We're exiting now!")


def main() -> None:
    for i in range(10):
        print(2**i)


if __name__ == "__main__":
    main()
    atexit.unregister(exit_handler)
    1 / 0
    
import atexit
import sqlite3

cxn = sqlite3.connect("db.sqlite3")


def init_db():
    cxn.execute("CREATE TABLE IF NOT EXISTS memes (id INTEGER PRIMARY KEY, meme TEXT)")
    print("Database initialised!")


@atexit.register
def exit_handler():
    cxn.commit()
    cxn.close()
    print("Closed database!")


if __name__ == "__main__":
    init_db()
    1 / 0
    ...