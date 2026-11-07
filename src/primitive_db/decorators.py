import time
from functools import wraps


def handle_db_errors(func):
    """Перехватывает ошибки при выполнении операций базы данных."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")

    return wrapper


def confirm_action(action_name):
    """Декоратор для подтверждения действия пользователя."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')

            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Декоратор для логирования времени выполнения функции."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()

        result = func(*args, **kwargs)

        end_time = time.monotonic()
        execution_time = end_time - start_time

        print(f"Функция {func.__name__} выполнилась за {execution_time:.3f} секунд")

        return result

    return wrapper


def create_cacher():
    """Создаёт замыкание для кэширования результатов по ключу."""
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()

        return cache[key]

    return cache_result
