import sqlite3
from dataclasses import dataclass
from typing import Any, Union, List, Optional
from pathlib import Path
from hrenpack.framework.flask.forms.inputs import InputGroup as HrenpackInputGroup, Input, ComboBoxInput, InputTypeExtended


@dataclass
class Column:
    name: str
    type: str
    nullable: bool
    default: Any
    primary_key: bool
    max_length: Optional[int] = None


def get_sqlite_schema(db_path: Union[str, Path], table_name: str) -> List[Column]:
    """Для SQLite базы данных"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Получаем информацию о таблице
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    result = []
    for column in columns:
        type_list = column[2].split("(")
        if len(type_list) == 2:
            type_name, max_length = type_list
            max_length = int(max_length.strip(")"))
        elif len(type_list) == 1:
            type_name = type_list[0]
            max_length = None
        else:
            raise ValueError
        result.append(Column(
            column[1],
            type_name,
            not column[3],
            column[4],
            bool(column[5]),
            max_length
        ))

    conn.close()
    return result




class InputGroup(HrenpackInputGroup):
    @classmethod
    def from_sqlite_table(cls, sqlite_db_path: Union[Path, str], table_name: str, *, lang: str = 'en', **kwargs):
        columns = get_sqlite_schema(sqlite_db_path, table_name)
        self = cls(rewrite_attrs=True, lang=lang)
        input_types: dict[str, InputTypeExtended] = kwargs.get('input_types', {})
        labels: dict[str, str] = kwargs.get('labels', {})
        for column in columns:
            if column.primary_key:
                continue
            input_type: InputTypeExtended = 'text'
            if column.name in input_types:
                input_type = input_types[column.name]
            else:
                match column.type:
                    case 'VARCHAR':
                        input_type = 'text'
                    case 'INTEGER':
                        input_type = 'number'
                    case 'BOOLEAN':
                        input_type = 'checkbox'
                    case 'TEXT':
                        input_type = 'text'
                    case 'BLOB':
                        input_type = 'file'
                    case _:
                        input_type = 'text'
            label = labels.get(column.name)
            if input_type == 'select':
                input_object = ComboBoxInput(column.name, label, required=not column.nullable,
                                             values=kwargs.get(f'{column.name}__values', {}))
            else:
                input_object = Input(column.name, input_type, label, required=not column.nullable)
            self.add(input_object)
        return self

