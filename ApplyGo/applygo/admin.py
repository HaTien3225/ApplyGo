# admin_setup_popup.py
import os
from flask import redirect, url_for, flash
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from markupsafe import Markup
from wtforms import FileField, SelectField
from wtforms.validators import DataRequired

from applygo import app, db
from applygo.models import (
    User, Company, Job, Application, CandidateProfile,
    UserRole, ApplicationStatus, JobStatus
)

import cloudinary
import cloudinary.uploader

# ------------------------------
# Config Cloudinary
# ------------------------------
cloudinary.config(
    cloud_name=app.config.get("CLOUDINARY_CLOUD_NAME"),
    api_key=app.config.get("CLOUDINARY_API_KEY"),
    api_secret=app.config.get("CLOUDINARY_API_SECRET")
)


# ------------------------------
# Base Admin Classes
# ------------------------------
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin():
            return redirect(url_for('login_admin'))
        return super().index()


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('login_admin'))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()


class AuthenticatedView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()

    def create_model(self, form):
        try:
            model = self.model()
            form.populate_obj(model)
            db.session.add(model)
            db.session.flush()

            # Upload ảnh đại diện User
            if hasattr(form, 'image') and form.image.data:
                upload_result = cloudinary.uploader.upload(form.image.data)
                model.image_url = upload_result['secure_url']

            # Upload logo Công ty
            if hasattr(form, 'logo') and form.logo.data:
                upload_result = cloudinary.uploader.upload(form.logo.data)
                model.logo_url = upload_result['secure_url']

            db.session.commit()
            flash(f"Tạo {self.model.__name__} thành công!", "success")
            return model
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi tạo {self.model.__name__}: {e}", "error")
            return False

    def update_model(self, form, model):
        try:
            form.populate_obj(model)

            if hasattr(form, 'image') and form.image.data:
                upload_result = cloudinary.uploader.upload(form.image.data)
                model.image_url = upload_result['secure_url']

            if hasattr(form, 'logo') and form.logo.data:
                upload_result = cloudinary.uploader.upload(form.logo.data)
                model.logo_url = upload_result['secure_url']

            db.session.commit()
            flash(f"Cập nhật {self.model.__name__} thành công!", "success")
            return True
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi cập nhật {self.model.__name__}: {e}", "error")
            return False

    def delete_model(self, model):
        try:
            db.session.delete(model)
            db.session.commit()
            flash(f"Xóa {self.model.__name__} thành công!", "success")
            return True
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi xóa {self.model.__name__}: {e}", "error")
            return False


# ------------------------------
# Helper: popup thumbnail
# ------------------------------
def popup_image_formatter(view, context, model, name):
    url = getattr(model, name, None)
    if not url:
        return ""
    return Markup(f"""
    <img src="{url}" style="max-height:50px; cursor:pointer;" 
         data-bs-toggle="modal" data-bs-target="#imageModal{model.id}" />
    <div class="modal fade" id="imageModal{model.id}" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-body text-center">
            <img src="{url}" style="width:100%;"/>
          </div>
        </div>
      </div>
    </div>
    """)


# ------------------------------
# User View
# ------------------------------
class UserView(AuthenticatedView):
    column_list = ["id", "username", "email", "role", "company.name", "candidate_profile.full_name", "image_url"]
    column_searchable_list = ["username", "email"]
    column_filters = ["role"]
    column_labels = {
        "username": "Tên đăng nhập",
        "email": "Email",
        "role": "Vai trò",
        "company.name": "Công ty",
        "candidate_profile.full_name": "Tên ứng viên",
        "image_url": "Ảnh đại diện"
    }
    column_formatters = {"image_url": popup_image_formatter}

    form_extra_fields = {"image": FileField("Ảnh đại diện")}
    form_overrides = {"role": SelectField}
    form_args = {
        "role": {
            "choices": [(r.name, r.value) for r in UserRole],
            "validators": [DataRequired()]
        }
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
    form_overrides = {"status": SelectField}
    form_args = {"status": {"choices": [(s.name, s.value) for s in ApplicationStatus]}}


# ------------------------------
# Job View
# ------------------------------
class JobView(AuthenticatedView):
    column_list = ["id", "title", "company.name", "location", "salary", "status", "created_at"]
    column_searchable_list = ["title", "company.name"]
    column_filters = ["company.name", "location", "status", "created_at"]
    column_labels = {
        "title": "Tiêu đề",
        "company.name": "Công ty",
        "location": "Địa điểm",
        "salary": "Mức lương",
        "status": "Trạng thái",
        "created_at": "Ngày tạo"
    }
    form_overrides = {"status": SelectField}
    form_args = {"status": {"choices": [(s.name, s.value) for s in JobStatus]}}


# ------------------------------
# Company View
# ------------------------------
class CompanyView(AuthenticatedView):
    column_list = ["id", "name", "address", "user.username", "logo_url"]
    column_searchable_list = ["name", "address"]
    column_labels = {
        "name": "Tên công ty",
        "address": "Địa chỉ",
        "user.username": "Người quản lý",
        "logo_url": "Logo"
    }
    column_formatters = {"logo_url": popup_image_formatter}
    form_extra_fields = {"logo": FileField("Logo công ty")}


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
admin = Admin(app, name="Quản lý ApplyGO", template_mode="bootstrap4", url='/admin', index_view=MyAdminIndexView())

admin.add_view(UserView(User, db.session, name="Người dùng"))
admin.add_view(CompanyView(Company, db.session, name="Công ty"))
admin.add_view(JobView(Job, db.session, name="Tin tuyển dụng"))
admin.add_view(ApplicationView(Application, db.session, name="Ứng tuyển"))
admin.add_view(CandidateProfileView(CandidateProfile, db.session, name="Hồ sơ ứng viên"))
admin.add_view(LogoutView(name="Đăng xuất", endpoint="logout"))
