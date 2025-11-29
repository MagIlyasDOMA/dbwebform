from pathlib import Path
from typing import Union
from flask import Flask, request, render_template, redirect, url_for


class App(Flask):
    def __init__(self, *args, port: int = 8000, model_class, form_class, **kwargs):
        self._init_kwargs(kwargs)
        super().__init__(*args, **kwargs)
        self.port = port
        self.ModelClass = model_class
        self.FormClass = form_class
        self.index = self.route('/')(self.index)
        self.title = kwargs.get('title', "Создание нового объекта")
        self.index_template = kwargs.get('index_template', 'index.html')

    @staticmethod
    def _init_kwargs(kwargs):
        folder = Path(__file__).parent.absolute()
        if 'template_folder' not in kwargs:
            kwargs['template_folder'] = str(folder / 'templates')
        if 'static_folder' not in kwargs:
            kwargs['static_folder'] = str(folder / 'static')

    def index(self):
        form = self.FormClass()
        if form.validate_on_submit():
            print(form.data)
        return render_template(self.index_template, form=form, title=self.title)

    def run(self, *args, **kwargs):
        if 'port' in kwargs:
            super().run(*args, **kwargs)
        super().run(*args, **kwargs, port=self.port)

