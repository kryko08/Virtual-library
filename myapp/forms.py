from xml.dom import ValidationErr
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField 
from wtforms.validators import (DataRequired, Length, ValidationError)

import re

from mongodb import mongo

class RegistrationForm(FlaskForm):
    first_name = StringField("first name", validators=[DataRequired(), Length(max=50)])
    second_name = StringField("second name", validators=[DataRequired(), Length(max=50)])
    user_name = StringField("uživatelské jméno", validators=[DataRequired(), Length(max=25)])

    birth_number = StringField("rodné číslo", validators=[DataRequired(), Length(max=15)])
    address = StringField("adresa", validators=[DataRequired(), Length(max=50)])
    
    password = PasswordField("heslo", validators=[DataRequired()])

    def validate_password(form, field):
        s = field.data
        has_upper = bool(re.match(r'\w*[A-Z]\w*', s))
        has_digit = bool(re.match(r'\d', s))
        if len(s) < 8 or len(s) > 50 or not has_upper or not has_digit:
            raise ValidationError('''Heslo musí obsahovat minimálně 8 znaků, minimálně 1 číslici a minimálně 1 velké písmeno. 
            Současně délka nesmí být delší než 50 znaků''')

    # Birth number is unique value
    def validate_birth_number(form, field):
        s = field.data
        birth_number_list = mongo.db.users.find(
            {
                "birth_number": s
            }
        )
        if len(birth_number_list) != 0:
            raise ValidationError("Účet s tímto rodným číslem již existuje")

    def validate_user_name(form, field):
        s = field.data
        username_already_taken = mongo.db.users.find(
            {
                "username": s
            }
        )
        if len(username_already_taken) != 0:
            raise ValidationError("Uživatelské jméno je již zabrané, použijte jiné.")

        
class LoginForm(FlaskForm):
    username = StringField("uživatelské jméno")
    password = PasswordField("heslo")