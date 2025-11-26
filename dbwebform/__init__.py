from pathlib import Path
from typing import Union
from flask import Flask, request, render_template, redirect, url_for


class App(Flask):
    def __init__(self, *args, port: int = 8000, model_class, form_class, **kwargs):
        folder = Path(__file__).parent.absolute()
        super().__init__(*args, **kwargs, template_folder=folder / 'templates', static_folder=folder / 'static')
        self.port = port
        self.ModelClass = model_class
        self.FormClass = form_class
        self.index = self.route('/')(self.index)

    def index(self):
        form = self.FormClass()
        if form.validate_on_submit():
            print(form.data)
        return render_template('index.html', form=form)

    def run(self, *args, **kwargs):
        if 'port' in kwargs:
            super().run(*args, **kwargs)
        super().run(*args, **kwargs, port=self.port)

