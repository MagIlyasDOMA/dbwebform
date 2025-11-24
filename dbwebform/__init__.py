from pathlib import Path
from typing import Union
from flask import Flask, request, render_template, redirect, url_for
from .db import InputGroup


class App(Flask):
    def __init__(self, *args, port: int = 8000, sqlite_db_path: Union[str, Path],
                 table_name: str, lang: str = 'en', **kwargs):
        folder = Path(__file__).parent.absolute()
        super().__init__(*args, **kwargs, template_folder=folder / 'templates', static_folder=folder / 'static')
        self.port = port
        self.index = self.route('/')(self.index)
        self.inputs = InputGroup.from_sqlite_table(sqlite_db_path, table_name, lang=lang, **kwargs)

    def index(self):
        domain = '/static' if self.debug else 'https://magilyasdoma.github.io'
        return render_template('index.html', form=self.inputs, domain=domain)
