import time
from time import sleep

def connect() -> None:
    time.sleep(1)
    raise Exception()


@retry(retries=3, delay=1)
def connect() -> None:
    time.sleep(1)
    raise Exception('Could not connect to internet...')

def main() -> None:
    connect()
    

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