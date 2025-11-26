#!/usr/bin/env python3
"""
Скрипт для автоматического создания модели и формы из таблицы БД
"""

import argparse, json, sys, jinja2
from pathlib import Path
from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class ModelFormGenerator:
    """Генератор моделей и форм из таблиц БД"""

    def __init__(self, database_url, config_path):
        self.database_url = database_url
        self.config = self.load_config(config_path)
        self.engine = create_engine(database_url)
        self.metadata = MetaData()
        self.Base = declarative_base()

        # Маппинг типов SQL на SQLAlchemy
        self.sql_type_mapping = {
            'VARCHAR': 'String',
            'TEXT': 'Text',
            'INTEGER': 'Integer',
            'BIGINT': 'BigInteger',
            'SMALLINT': 'SmallInteger',
            'BOOLEAN': 'Boolean',
            'DATE': 'Date',
            'DATETIME': 'DateTime',
            'TIMESTAMP': 'DateTime',
            'FLOAT': 'Float',
            'DECIMAL': 'Decimal',
            'NUMERIC': 'Numeric',
            'BLOB': 'LargeBinary'
        }

        # Маппинг типов SQL на WTForms
        self.form_type_mapping = {
            'VARCHAR': 'StringField',
            'TEXT': 'TextAreaField',
            'INTEGER': 'IntegerField',
            'BIGINT': 'IntegerField',
            'SMALLINT': 'IntegerField',
            'BOOLEAN': 'BooleanField',
            'DATE': 'DateField',
            'DATETIME': 'DateTimeField',
            'TIMESTAMP': 'DateTimeField',
            'FLOAT': 'FloatField',
            'DECIMAL': 'DecimalField',
            'NUMERIC': 'DecimalField'
        }

    def load_config(self, config_path):
        """Загружает конфигурацию из JSON файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            sys.exit(1)

    def get_table_info(self, table_name):
        """Получает информацию о таблице"""
        try:
            inspector = inspect(self.engine)

            # Получаем колонки
            columns = inspector.get_columns(table_name)

            # Получаем первичные ключи
            pk_columns = inspector.get_pk_constraint(table_name)['constrained_columns']

            # Получаем внешние ключи
            fks = inspector.get_foreign_keys(table_name)

            return {
                'columns': columns,
                'primary_keys': pk_columns,
                'foreign_keys': fks,
                'table_name': table_name
            }
        except Exception as e:
            print(f"Ошибка получения информации о таблице {table_name}: {e}")
            return None

    def generate_model_code(self, table_info):
        """Генерирует код модели SQLAlchemy"""
        template_str = '''
from sqlalchemy import Column, {{ column_types|join(', ') }}
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class {{ class_name }}(Base):
    __tablename__ = '{{ table_name }}'

    {% for column in columns %}
    {{ column.name }} = Column({{ column.type_expression }}{% if column.primary_key %}, primary_key=True{% endif %}{% if not column.nullable %}, nullable=False{% endif %}{% if column.unique %}, unique=True{% endif %}{% if column.default %}, default={{ column.default }}{% endif %})
    {% endfor %}

    def __repr__(self):
        return f"<{{ class_name }}({', '.join([f'{col.name}={{self.{col.name}!r}}' for col in columns if col.primary_key])})>"
'''

        # Подготавливаем данные для шаблона
        columns_data = []
        column_types = set()

        for column in table_info['columns']:
            col_type = type(column['type']).__name__
            sqlalchemy_type = self.sql_type_mapping.get(col_type, 'String')
            column_types.add(sqlalchemy_type)

            # Формируем выражение типа
            type_expression = sqlalchemy_type
            if hasattr(column['type'], 'length') and column['type'].length:
                type_expression += f"({column['type'].length})"

            columns_data.append({
                'name': column['name'],
                'type_expression': type_expression,
                'primary_key': column['name'] in table_info['primary_keys'],
                'nullable': column['nullable'],
                'unique': column.get('unique', False),
                'default': column.get('default')
            })

        # Добавляем необходимые типы
        column_types = ['String', 'Integer']  # Базовые типы

        # Рендерим шаблон
        template = jinja2.Template(template_str)
        class_name = self.get_class_name(table_info['table_name'])

        return template.render(
            class_name=class_name,
            table_name=table_info['table_name'],
            columns=columns_data,
            column_types=column_types
        )

    def generate_form_code(self, table_info):
        """Генерирует код формы WTForms"""
        template_str = '''
from flask_wtf import FlaskForm
from wtforms import {{ field_types|join(', ') }}
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange

class {{ form_class_name }}(FlaskForm):
    {% for field in fields %}
    {{ field.name }} = {{ field.type }}('{{ field.label }}', validators=[{{ field.validators }}])
    {% endfor %}
    submit = SubmitField('{{ submit_text }}')
'''

        # Подготавливаем данные для шаблона
        fields_data = []
        field_types = set(['SubmitField'])

        for column in table_info['columns']:
            # Пропускаем auto-increment поля
            if column.get('autoincrement', False):
                continue

            col_type = type(column['type']).__name__
            field_type = self.form_type_mapping.get(col_type, 'StringField')
            field_types.add(field_type)

            # Определяем валидаторы
            validators = []
            if not column['nullable'] and not column.get('autoincrement', False):
                validators.append('DataRequired()')
            else:
                validators.append('Optional()')

            # Добавляем специфичные валидаторы
            if col_type == 'VARCHAR' and hasattr(column['type'], 'length'):
                validators.append(f"Length(max={column['type'].length})")
            elif col_type in ['INTEGER', 'BIGINT', 'SMALLINT']:
                validators.append('NumberRange(min=0)')

            # Проверяем email по имени поля
            if 'email' in column['name'].lower():
                validators.append('Email()')

            fields_data.append({
                'name': column['name'],
                'type': field_type,
                'label': self.get_field_label(column['name']),
                'validators': ', '.join(validators)
            })

        # Рендерим шаблон
        template = jinja2.Template(template_str)
        form_class_name = self.get_form_class_name(table_info['table_name'])

        return template.render(
            form_class_name=form_class_name,
            fields=fields_data,
            field_types=list(field_types),
            submit_text=self.config.get('submit_text', 'Сохранить')
        )

    def get_class_name(self, table_name):
        """Преобразует имя таблицы в имя класса"""
        # Убираем префиксы/суффиксы из конфигурации
        table_name = table_name.lower()
        remove_prefixes = self.config.get('remove_prefixes', [])
        remove_suffixes = self.config.get('remove_suffixes', [])

        for prefix in remove_prefixes:
            if table_name.startswith(prefix.lower()):
                table_name = table_name[len(prefix):]

        for suffix in remove_suffixes:
            if table_name.endswith(suffix.lower()):
                table_name = table_name[:-len(suffix)]

        # Capitalize и убираем подчеркивания
        return ''.join(word.capitalize() for word in table_name.split('_'))

    def get_form_class_name(self, table_name):
        """Преобразует имя таблицы в имя класса формы"""
        class_name = self.get_class_name(table_name)
        return f"{class_name}Form"

    def get_field_label(self, field_name):
        """Преобразует имя поля в читаемую метку"""
        # Заменяем подчеркивания на пробелы и capitalize
        return ' '.join(word.capitalize() for word in field_name.split('_'))

    def generate_files(self, table_name, output_dir='output'):
        """Генерирует файлы модели и формы"""
        # Создаем директорию для выходных файлов
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Получаем информацию о таблице
        table_info = self.get_table_info(table_name)
        if not table_info:
            return False

        # Генерируем код
        model_code = self.generate_model_code(table_info)
        form_code = self.generate_form_code(table_info)

        # Имена файлов
        class_name = self.get_class_name(table_name)
        model_filename = f"{output_path}/{class_name.lower()}_model.py"
        form_filename = f"{output_path}/{class_name.lower()}_form.py"

        # Сохраняем файлы
        try:
            with open(model_filename, 'w', encoding='utf-8') as f:
                f.write(model_code)

            with open(form_filename, 'w', encoding='utf-8') as f:
                f.write(form_code)

            print(f"✅ Модель создана: {model_filename}")
            print(f"✅ Форма создана: {form_filename}")
            return True

        except Exception as e:
            print(f"❌ Ошибка сохранения файлов: {e}")
            return False


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description='Генератор моделей и форм из таблиц БД')
    parser.add_argument('database_url', help='URL базы данных (например: sqlite:///example.db)')
    parser.add_argument('table_name', help='Имя таблицы для генерации')
    parser.add_argument('config_path', help='Путь к JSON файлу конфигурации')
    parser.add_argument('--output-dir', default='output', help='Директория для выходных файлов')

    args = parser.parse_args()

    # Проверяем существование конфигурационного файла
    if not Path(args.config_path).exists():
        print(f"❌ Конфигурационный файл не найден: {args.config_path}")
        sys.exit(1)

    # Создаем генератор
    generator = ModelFormGenerator(args.database_url, args.config_path)

    # Генерируем файлы
    success = generator.generate_files(args.table_name, args.output_dir)

    if success:
        print("🎉 Генерация завершена успешно!")
    else:
        print("💥 Генерация завершена с ошибками!")
        sys.exit(1)


if __name__ == '__main__':
    main()