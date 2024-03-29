from os import listdir
from os.path import isfile, join

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired

from wtforms import SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Regexp, NumberRange

from migrator import CONFIG_DIR


class ConfigForm(FlaskForm):
    config = FileField(
        validators=[
            FileRequired(),
            FileAllowed(['ti.ru'], 'File with .ti.ru suffix only')
        ],
        render_kw={"class": "form-control"}
    )


class HostnameForm(FlaskForm):
    hostname = SelectField(
        validators=[DataRequired(message='The field is required')],
        render_kw={'class': 'form-select'},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fill_choices()

    def fill_choices(self):
        choices = [
            (f, f) for f in listdir(CONFIG_DIR)
            if isfile(join(CONFIG_DIR, f)) and '.ti.ru' in f
        ]
        choices = [('', '')] + choices
        self.hostname.choices = choices


class InputForm(FlaskForm):
    min_outer_tag_l = 1
    max_outer_tag_l = 4094

    render_kw = {'class': 'form-control'}
    hostname = SelectField(
        validators=[DataRequired(message='The field is required')],
        render_kw={'class': 'form-select'},
    )

    interface = StringField(
        validators=[
            DataRequired(message='The field is required'),
            Regexp(regex=r'\d/\d/\d', message='Wrong interface format'),
        ],
        render_kw=render_kw
    )

    outer_tag = IntegerField(
        validators=[
            DataRequired(),
            NumberRange(
                min=min_outer_tag_l,
                max=max_outer_tag_l,
                message=f'From {min_outer_tag_l} to {max_outer_tag_l} value'
            ),

        ],
        render_kw=render_kw
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fill_choices()

    def fill_choices(self):
        choices = [
            (f, f) for f in listdir(CONFIG_DIR)
            if isfile(join(CONFIG_DIR, f)) and '.ti.ru' in f
        ]
        choices = [('', '')] + choices
        self.hostname.choices = choices
