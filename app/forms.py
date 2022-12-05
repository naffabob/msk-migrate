from os import listdir
from os.path import isfile, join

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, IntegerField
from wtforms.validators import DataRequired, Regexp, NumberRange

from migrator import CONFIG_DIR


class InputForm(FlaskForm):
    min_outer_tag_l = 1
    max_outer_tag_l = 4094

    render_kw = {'class': 'form-control'}
    hostname = SelectField(
        label='Choose hostname',
        validators=[DataRequired(message='The field is required')],
        render_kw=render_kw,
    )

    interface = StringField(
        label='Interface, ex.: 0/3/0',
        validators=[
            DataRequired(message='The field is required'),
            Regexp(regex=r'\d/\d/\d', message='Wrong interface format'),
        ],
        render_kw=render_kw
    )

    outer_tag = IntegerField(
        label='Outer tag, ex.: 364',
        validators=[
            DataRequired(),
            NumberRange(
                min=min_outer_tag_l,
                max=max_outer_tag_l,
                message=f'From {min_outer_tag_l} to {max_outer_tag_l} characters'
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
