import json
from pathlib import Path

from .constants import DATA_DIR


def load_metadata(filepath):
    """Загружает метаданные из JSON-файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            metadata = json.load(file)
        return metadata
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_table_data(table_name):
    """Загружает записи таблицы из JSON-файла."""
    filepath = Path(DATA_DIR) / f"{table_name}.json"
    try:
        with open(filepath, "r", encoding="utf-8") as table:
            table_data = json.load(table)
        return table_data
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет записи таблицы в JSON-файл."""
    Path(DATA_DIR).mkdir(exist_ok=True)
    filepath = Path(DATA_DIR) / f"{table_name}.json"

    with open(filepath, "w", encoding="utf-8") as table:
        json.dump(data, table, ensure_ascii=False, indent=4)


def delete_table_data(table_name):
    """Удаляет JSON-файл с записями таблицы."""
    filepath = Path(DATA_DIR) / f"{table_name}.json"
    filepath.unlink(missing_ok=True)
