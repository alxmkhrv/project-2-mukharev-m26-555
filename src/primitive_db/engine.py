import shlex

import prompt
from prettytable import PrettyTable

from .constants import META_FILE
from .core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
)
from .decorators import create_cacher
from .utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> "
        "<столбец1:тип> <столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> "
        "values (<значение1>, <значение2>, ...) - создать запись"
    )
    print(
        "<command> select from <имя_таблицы> "
        "where <столбец> = <значение> - прочитать записи по условию"
    )
    print("<command> select from <имя_таблицы> - прочитать все записи")
    print(
        "<command> update <имя_таблицы> set <столбец> = <новое_значение> "
        "where <столбец_условия> = <значение> - обновить запись"
    )
    print(
        "<command> delete from <имя_таблицы> "
        "where <столбец> = <значение> - удалить запись"
    )
    print("<command> info <имя_таблицы> - информация о таблице")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def parse_value(value):
    value = value.strip()

    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.startswith(("'", '"')) and value.endswith(("'", '"')):
        return value[1:-1]

    return int(value)


def parse_condition(condition):
    column, value = condition.split("=", 1)
    return {column.strip(): parse_value(value)}


def run():
    print_help()
    cache_result = create_cacher()

    while True:
        metadata = load_metadata(META_FILE)

        user_input = prompt.string("Введите команду: ")
        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Ошибка: Проверьте правильность кавычек.")
            continue
        if not args:
            continue
        command = args[0]
        if command == "help":
            if len(args) != 1:
                print("Некорректное количество аргументов.")
                continue
            print_help()

        elif command == "exit":
            if len(args) != 1:
                print("Некорректное количество аргументов.")
                continue
            break

        elif command == "list_tables":
            if len(args) != 1:
                print("Некорректное количество аргументов.")
                continue
            list_tables(metadata)

        elif command == "create_table":
            if len(args) < 3:
                print("Некорректное количество аргументов.")
                continue

            old_count = len(metadata)
            create_table(metadata, args[1], args[2:])
            if len(metadata) > old_count:
                save_metadata(META_FILE, metadata)
                cache_result = create_cacher()
                columns = metadata[args[1]]
                column_description = []
                for name, column_type in columns.items():
                    column_description.append(f"{name}:{column_type}")
                result = ", ".join(column_description)
                print(f'Таблица "{args[1]}" успешно создана со столбцами: {result}')

        elif command == "drop_table":
            if len(args) != 2:
                print("Некорректное количество аргументов.")
                continue
            tables_before_delete = len(metadata)
            drop_table(metadata, args[1])
            if len(metadata) < tables_before_delete:
                save_metadata(META_FILE, metadata)
                cache_result = create_cacher()

        elif command == "insert":
            if len(args) < 4 or args[1] != "into" or args[3] != "values":
                print("Ошибка: Некорректная команда insert.")
                continue
            try:
                table_name = args[2]
                raw_values = user_input.split("(", 1)[1].rsplit(")", 1)[0]
                values = [parse_value(value) for value in raw_values.split(",")]

                updated_data = insert(metadata, table_name, values)

                if updated_data is not None:
                    save_table_data(table_name, updated_data)
                    cache_result = create_cacher()
                    print(
                        f"Запись с ID={updated_data[-1]['ID']} "
                        f'успешно добавлена в таблицу "{table_name}".'
                    )
            except (IndexError, ValueError):
                print("Ошибка: Некорректная команда insert.")

        elif command == "select":
            if len(args) < 3 or args[1] != "from":
                print("Ошибка: Некорректная команда select.")
                continue

            table_name = args[2]

            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue

            where_clause = None

            if len(args) > 3:
                try:
                    if args[3] != "where":
                        raise ValueError
                    condition = user_input.split(" where ", 1)[1]
                    where_clause = parse_condition(condition)
                except (IndexError, ValueError):
                    print("Ошибка: Некорректное условие WHERE.")
                    continue

            cache_key = (
                table_name,
                tuple(where_clause.items()) if where_clause else None,
            )

            result = cache_result(
                cache_key, lambda: select(load_table_data(table_name), where_clause)
            )

            if result is None:
                continue

            table = PrettyTable()
            table.field_names = list(metadata[table_name])
            table.add_rows(
                [[row[column] for column in table.field_names] for row in result]
            )

            print(table)

        elif command == "update":
            try:
                table_name = args[1]
                set_text, where_text = user_input.split(" set ", 1)[1].split(
                    " where ", 1
                )
                set_clause = parse_condition(set_text)
                where_clause = parse_condition(where_text)

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                column, value = next(iter(set_clause.items()))
                where_column, where_value = next(iter(where_clause.items()))
                columns = metadata[table_name]

                if column not in columns or where_column not in columns:
                    print("Ошибка: Столбец не существует.")
                    continue

                if column == "ID":
                    print("Ошибка: Изменение ID запрещено.")
                    continue

                types = {"int": int, "str": str, "bool": bool}

                if (
                    type(value) is not types[columns[column]]
                    or type(where_value) is not types[columns[where_column]]
                ):
                    print("Ошибка: Неверный тип значения.")
                    continue

                table_data = load_table_data(table_name)
                updated_data = update(table_data, set_clause, where_clause)

                if updated_data is None:
                    continue

                save_table_data(table_name, updated_data)
                cache_result = create_cacher()

                print(f'Данные таблицы "{table_name}" обновлены.')

            except (IndexError, ValueError):
                print("Ошибка: Некорректная команда update.")

        elif command == "delete":
            if len(args) < 4 or args[1] != "from" or args[3] != "where":
                print("Ошибка: Некорректная команда delete.")
                continue

            table_name = args[2]

            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue

            try:
                condition = user_input.split(" where ", 1)[1]
                where_clause = parse_condition(condition)
            except (IndexError, ValueError):
                print("Ошибка: Некорректное условие WHERE.")
                continue

            table_data = load_table_data(table_name)
            updated_data = delete(table_data, where_clause)

            if updated_data is None:
                continue

            deleted_count = len(table_data) - len(updated_data)

            if deleted_count > 0:
                save_table_data(table_name, updated_data)
                cache_result = create_cacher()
                print(f"Удалено записей: {deleted_count}.")
            else:
                print("Записи не найдены.")

        elif command == "info":
            if len(args) != 2:
                print("Ошибка: Некорректная команда info.")
                continue

            table_name = args[1]

            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue

            columns = metadata[table_name]
            table_data = load_table_data(table_name)

            print(f"Таблица: {table_name}")
            print(
                "Столбцы: "
                + ", ".join(f"{name}:{type_}" for name, type_ in columns.items())
            )
            print(f"Количество записей: {len(table_data)}")

        else:
            print(f"Функции {command} нет. Попробуйте снова.")
