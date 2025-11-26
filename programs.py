__all__ = []

# Модель SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

__all__ += ['Model']

db = SQLAlchemy()


class Model(db.Model):
    __tablename__ = 'programs'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    language = db.Column(db.String(100), nullable=False)
    download_link = db.Column(db.String(255), nullable=False)
    install_link = db.Column(db.String(255))
    version = db.Column(db.String(10))
    type = db.Column(db.String(7), nullable=False)

    def __repr__(self):
        return f'<Model {self.id}>'


# Форма WTForms
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, FloatField, BooleanField, DateField, DateTimeField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange

__all__ += ['ModelForm']

class ModelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    language = StringField('Language', validators=[DataRequired(), Length(max=100)])
    download_link = StringField('Download Link', validators=[DataRequired(), Length(max=255)])
    install_link = StringField('Install Link', validators=[Length(max=255)])
    version = StringField('Version', validators=[Length(max=10)])
    type = StringField('Type', validators=[DataRequired(), Length(max=7)])
    submit = SubmitField('Отправить')
