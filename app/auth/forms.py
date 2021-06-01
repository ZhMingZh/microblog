from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, EqualTo, Email
from app.models import User
from flask_babel import lazy_gettext as _l


class LoginForm(FlaskForm):
    """登录表单"""
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    """注册表单"""
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(username=email.data).first()
        if user is not None:
            raise ValidationError(_l('Please use a different email.'))


class ResetPasswordRequestForm(FlaskForm):
    """重置密码请求的表单"""
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Reset Password Request'))


class ResetPasswordForm(FlaskForm):
    """重置密码的表单"""
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Repeat Password'), validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))
