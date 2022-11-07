from xml.dom import ValidationErr
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import (DataRequired, Length, ValidationError)

import re

from .mongodb import mongo


# User Forms
class PasswordCheck():
    def __init__(self, message = None):
        if not message:
            message = "Heslo musí obsahovat alespoň 1 velké písmeno a 1 číslici"
        self.message = message

    
    def __call__(self, form, field):
        s = field.data
        has_upper = bool(re.match(r'\w*[A-Z]\w*', s))
        has_digit = bool(re.match(r'.*[0-9].*', s))
        if not has_digit or not has_upper:
            raise ValidationError(self.message)


class BirthNumberCheck():
    def __init__(self, message = None):
        if not message:
            message = "Uživatel s tímto rodným číslem je již zaregistrovaný."
        self.message = message

    def __call__(self, form, field):
        s = field.data
        birth_number_list = mongo.db.users.find_one(
            {
                "birth_number": s
            }
        )
        if birth_number_list:
            raise ValidationError(self.message)


class UsernameCheck():
    def __init__(self, message = None):
        if not message:
            message = "Toto uživatelské jméno je již zabrané, zkuste jiné."
        self.message = message
    
    def __call__(self, form, field):
        s = field.data
        username_already_taken = mongo.db.users.find_one(
            {
                "username": s
            }
        )
        if username_already_taken:
            raise ValidationError(self.message)


class RegistrationForm(FlaskForm):
    first_name = StringField("Jméno", validators=[DataRequired(), Length(min= 2, max=50)])
    second_name = StringField("Příjmení", validators=[DataRequired(), Length(min = 2, max=50)])
    user_name = StringField("Uživatelské jméno", validators=[DataRequired(), Length(min = 5, max=25), UsernameCheck()])

    birth_number = StringField("Rodné číslo", validators=[DataRequired(), Length(max=15), BirthNumberCheck()])
    address = StringField("Adresa", validators=[DataRequired(), Length(max=50)])
    
    password = PasswordField("Heslo", validators=[DataRequired(), PasswordCheck(), Length(min=8, max=50)])


class LoginForm(FlaskForm):
    username = StringField("uživatelské jméno", validators = [DataRequired()])
    password = PasswordField("heslo", validators = [DataRequired()])
    submit = SubmitField("Přihlásit se")

# ------------------------
# Admin Forms
class UserVerificationForm(FlaskForm):
    first_name = StringField("first name", validators=[DataRequired(), Length(min= 2, max=50)])
    second_name = StringField("second name", validators=[DataRequired(), Length(min = 2, max=50)])
    user_name = StringField("uživatelské jméno", validators=[DataRequired(), Length(min = 5, max=25)])

    birth_number = StringField("rodné číslo", validators=[DataRequired(), Length(max=15)])
    address = StringField("adresa", validators=[DataRequired(), Length(max=50)])  
