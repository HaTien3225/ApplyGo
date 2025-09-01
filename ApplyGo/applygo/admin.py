# admin_setup.py
from flask import redirect, url_for
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from applygo import app, db
from applygo.models import User, Company, Job, Application, CandidateProfile

# ------------------------------
# Custom Admin Index View
# ------------------------------
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin():
            return redirect(url_for('login_admin'))
        return super().index()

# ------------------------------
# Logout View
# ------------------------------
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('login_admin'))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

# ------------------------------
# Base ModelView cho admin
# ------------------------------
class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

# ------------------------------
# User View
# ------------------------------
class UserView(AuthenticatedView):
    column_list = ["id", "username", "email", "role", "company.name", "candidate_profile.full_name"]
    column_searchable_list = ["username", "email"]
    column_filters = ["role"]
    column_labels = {
        "username": "Tên đăng nhập",
        "email": "Email",
        "role": "Vai trò",
        "company.name": "Công ty",
        "candidate_profile.full_name": "Tên ứng viên"
    }

# ------------------------------
# Company View
# ------------------------------
class CompanyView(AuthenticatedView):
    column_list = ["id", "name", "address", "user.username"]
    column_searchable_list = ["name", "address"]
    column_labels = {
        "name": "Tên công ty",
        "address": "Địa chỉ",
        "user.username": "Người quản lý"
    }

# ------------------------------
# Job View
# ------------------------------
class JobView(AuthenticatedView):
    column_list = ["id", "title", "company.name", "location", "salary", "created_at"]
    column_searchable_list = ["title", "company.name"]
    column_filters = ["company.name", "location", "created_at"]
    column_labels = {
        "title": "Tiêu đề",
        "company.name": "Công ty",
        "location": "Địa điểm",
        "salary": "Mức lương",
        "created_at": "Ngày tạo"
    }

# ------------------------------
# Application View
# ------------------------------
class ApplicationView(AuthenticatedView):
    column_list = ["id", "candidate_profile.full_name", "job.title", "status", "applied_at"]
    column_searchable_list = ["candidate_profile.full_name", "job.title"]
    column_filters = ["status"]
    column_labels = {
        "candidate_profile.full_name": "Ứng viên",
        "job.title": "Tin tuyển dụng",
        "status": "Trạng thái",
        "applied_at": "Ngày nộp"
    }

# ------------------------------
# CandidateProfile View
# ------------------------------
class CandidateProfileView(AuthenticatedView):
    column_list = ["id", "full_name", "user.username", "phone", "skills", "experience", "education"]
    column_searchable_list = ["full_name", "user.username"]
    column_labels = {
        "full_name": "Họ và tên",
        "user.username": "Tên đăng nhập",
        "phone": "Số điện thoại",
        "skills": "Kỹ năng",
        "experience": "Kinh nghiệm",
        "education": "Học vấn"
    }

# ------------------------------
# Setup Admin
# ------------------------------
admin = Admin(
    app,
    name="Quản lý ApplyGO",
    template_mode="bootstrap4",
    url='/admin',                 # Đây là URL chính cho admin
    index_view=MyAdminIndexView()
)

# Thêm các view
admin.add_view(UserView(User, db.session, name="Người dùng"))
admin.add_view(CompanyView(Company, db.session, name="Công ty"))
admin.add_view(JobView(Job, db.session, name="Tin tuyển dụng"))
admin.add_view(ApplicationView(Application, db.session, name="Ứng tuyển"))
admin.add_view(CandidateProfileView(CandidateProfile, db.session, name="Hồ sơ ứng viên"))
admin.add_view(LogoutView(name="Đăng xuất", endpoint="logout"))
