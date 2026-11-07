from .constants import VALID_TYPES
from .decorators import confirm_action, handle_db_errors, log_time
from .utils import delete_table_data, load_table_data


def create_table(metadata, table_name, columns):
    """Создаёт таблицу с заданными столбцами и типами данных."""
    table_name = table_name.strip()
    if not table_name:
        print("Ошибка: Название таблицы не может быть пустым.")
        return metadata
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    table_columns = {"ID": "int"}
    used_columns = []
    for data in columns:
        if data.count(":") != 1:
            print("Ошибка: Некорректный формат данных.")
            return metadata
        column_name, column_type = data.split(":")
        column_name = column_name.strip()
        if not column_name:
            print("Ошибка: Название столбца не может быть пустым.")
            return metadata
        if column_name in used_columns:
            print("Ошибка: Название столбца не может повторяться.")
            return metadata
        if column_type not in VALID_TYPES:
            print(f"Некорректное значение: {column_type}. Попробуйте снова.")
            return metadata
        if column_name == "ID":
            print("Ошибка: Столбец ID создаётся автоматически.")
            return metadata

        used_columns.append(column_name)

        table_columns[column_name] = column_type
    metadata[table_name] = table_columns
    return metadata


@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу и связанный с ней JSON-файл."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    delete_table_data(table_name)

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Выводит список существующих таблиц."""
    if not metadata:
        print("В базе данных пока нет таблиц.")
        return
    for table_name in metadata:
        print(f"- {table_name}")


@log_time
@handle_db_errors
def insert(metadata, table_name, values):
    """Добавляет запись в таблицу с автоматически созданным ID."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None
    expected_values = len(metadata[table_name]) - 1
    if expected_values != len(values):
        print(f"Ошибка: Ожидалось {expected_values} значения, получено {len(values)}")
        return None

    columns = list(metadata[table_name].items())[1:]
    type_map = {
        "int": int,
        "str": str,
        "bool": bool,
    }
    for (name, column_type), value in zip(columns, values):
        expected_type = type_map[column_type]
        if type(value) is not expected_type:
            print(f"Некорректное значение: {value}. Попробуйте снова.")
            return None
    table_data = load_table_data(table_name)
    new_id = max((row["ID"] for row in table_data), default=0) + 1
    new_record = {"ID": new_id}
    for (name, _), value in zip(columns, values):
        new_record[name] = value
    table_data.append(new_record)
    return table_data


@log_time
@handle_db_errors
def select(table_data, where_clause=None):
    """Возвращает записи таблицы с учётом условия WHERE."""
    if where_clause is None:
        return table_data

    column, value = next(iter(where_clause.items()))
    result = []

    for row in table_data:
        if row.get(column) == value:
            result.append(row)

    return result


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет записи, соответствующие условию WHERE."""
    set_column, new_value = next(iter(set_clause.items()))
    where_column, where_value = next(iter(where_clause.items()))

    for row in table_data:
        if row.get(where_column) == where_value:
            row[set_column] = new_value

    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет записи, соответствующие условию WHERE."""
    column, value = next(iter(where_clause.items()))

    result = []

    for row in table_data:
        if row.get(column) != value:
            result.append(row)

    return result
