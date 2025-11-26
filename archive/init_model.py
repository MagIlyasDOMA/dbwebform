import argparse, sys
from sqlacodegen.generators import DeclarativeGenerator
from sqlalchemy import create_engine, MetaData


def generate_model(db_url: str, table_name: str):
    engine = create_engine(db_url)
    metadata = MetaData()
    metadata.reflect(engine, only=[table_name])
    generator = DeclarativeGenerator(metadata, engine, [])
    with open('models.py', 'w') as file:
        file.write(generator.generate())
    print("Создание модели таблицы базы данных завершено")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('db_url', type=str, help="URL базы данных")
    parser.add_argument('table_name', type=str, help="Название таблицы")
    if len(sys.argv) == 1:
        parser.print_help()
    args = parser.parse_args()
    generate_model(args.db_url, args.table_name)


if __name__ == "__main__":
    main()

