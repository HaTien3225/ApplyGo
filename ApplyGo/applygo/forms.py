from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class EmployerRegisterForm(FlaskForm):
    company_name = StringField("Tên công ty", validators=[DataRequired(), Length(max=100)])
    address = StringField("Địa chỉ công ty")
    website = StringField("Website")
    mst = StringField("Mã số thuế", validators=[DataRequired(), Length(max=10)])
    submit = SubmitField("Đăng ký Nhà tuyển dụng")
