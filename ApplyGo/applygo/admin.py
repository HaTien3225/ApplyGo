import cloudinary
import cloudinary.uploader
from datetime import datetime, timedelta
from flask import redirect, url_for, flash, request
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from markupsafe import Markup
from wtforms import FileField, SelectField
from wtforms.validators import DataRequired
from sqlalchemy import extract, func
from applygo import app, db
from applygo.models import (
    User, Company, Job, Application, CandidateProfile,
    UserRole, ApplicationStatus, JobStatus
)


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin():
            return redirect(url_for("login_admin"))
        return super().index()


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for("login_admin"))

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

            if hasattr(form, "image") and form.image.data:
                upload_result = cloudinary.uploader.upload(form.image.data)
                model.image_url = upload_result["secure_url"]
            if hasattr(form, "logo") and form.logo.data:
                upload_result = cloudinary.uploader.upload(form.logo.data)
                model.logo_url = upload_result["secure_url"]

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
            if hasattr(form, "image") and form.image.data:
                upload_result = cloudinary.uploader.upload(form.image.data)
                model.image_url = upload_result["secure_url"]
            if hasattr(form, "logo") and form.logo.data:
                upload_result = cloudinary.uploader.upload(form.logo.data)
                model.logo_url = upload_result["secure_url"]

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


from flask import url_for
from markupsafe import Markup


def popup_image_formatter(view, context, model, name, folder="Image"):
    """
    Formatter ảnh cho Flask-Admin:
    - Nếu url đầy đủ (http...), dùng trực tiếp
    - Nếu url local, thêm url_for với thư mục folder
    """
    url = getattr(model, name, None)
    if not url:
        return ""

    if not url.startswith("http"):
        url = url_for('static', filename=f'{folder}/{url}')

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


class CompanyApprovalView(AuthenticatedView):
    column_list = ["id", "name", "address", "website", "mst", "status", "user.username", "logo_url"]
    column_labels = {
        "name": "Tên công ty",
        "address": "Địa chỉ",
        "website": "Website",
        "mst": "Mã số thuế",
        "status": "Trạng thái",
        "user.username": "Người quản lý",
        "logo_url": "Logo"
    }
    column_formatters = {
        "logo_url": lambda v, c, m, n: popup_image_formatter(v, c, m, n, folder="Image/logos")
    }

    form_overrides = {"status": SelectField}
    form_args = {
        "status": {
            "choices": [
                ("Pending", "Chờ duyệt"),
                ("Approved", "Đã duyệt"),
                ("Rejected", "Từ chối")
            ],
            "validators": [DataRequired()]
        }
    }

    def update_model(self, form, model):
        try:
            old_status = model.status
            form.populate_obj(model)

            db.session.commit()
            flash(f"Cập nhật trạng thái công ty {model.name} thành công!", "success")

            if old_status != "Approved" and model.status == "Approved":
                if model.user and model.user.role != "company":
                    model.user.role = "company"
                    db.session.commit()
                    flash(f"Người dùng {model.user.username} đã trở thành Nhà tuyển dụng!", "info")

            return True
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi duyệt công ty: {e}", "error")
            return False


class UserView(AuthenticatedView):
    column_list = ["id", "username", "email", "role", "company.name",
                   "candidate_profile.full_name", "image_url"]
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
    column_formatters = {
        "image_url": lambda v, c, m, n: popup_image_formatter(v, c, m, n, folder="Image/avatars")
    }
    form_extra_fields = {"image": FileField("Ảnh đại diện")}
    form_overrides = {"role": SelectField}
    form_args = {
        "role": {
            "choices": [(r.name, r.value) for r in UserRole],
            "validators": [DataRequired()]
        }
    }


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
    form_args = {
        "status": {
            "choices": [(s.name, s.value) for s in ApplicationStatus],
            "validators": [DataRequired()]
        }
    }


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
    form_args = {
        "status": {
            "choices": [(s.name, s.value) for s in JobStatus],
            "validators": [DataRequired()]
        }
    }


class CompanyView(AuthenticatedView):
    column_list = ["id", "name", "address", "user.username", "logo_url"]
    column_searchable_list = ["name", "address"]
    column_labels = {
        "name": "Tên công ty",
        "address": "Địa chỉ",
        "user.username": "Người quản lý",
        "logo_url": "Logo"
    }
    column_formatters = {
        "logo_url": lambda v, c, m, n: popup_image_formatter(v, c, m, n, folder="Image/logos")
    }
    form_extra_fields = {"logo": FileField("Logo công ty")}


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


class ReportView(BaseView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin():
            return redirect(url_for("login_admin"))

        months = int(request.args.get('months', 6))
        now = datetime.now()
        start_date = datetime.min if months == 0 else now - timedelta(days=30 * months)

        location_filter = request.args.get('location', 'all')
        all_locations = [loc[0] for loc in Job.query.with_entities(Job.location).distinct()]

        total_users = User.query.count()
        total_candidates = User.query.filter_by(role="candidate").count()
        total_companies = User.query.filter_by(role="company").count()
        total_jobs = Job.query.count()
        total_applications = Application.query.count()
        total_approved_companies = Company.query.filter_by(status="Approved").count()

        month_labels = db.session.query(
            extract('year', Application.applied_at).label('year'),
            extract('month', Application.applied_at).label('month')
        ).filter(Application.applied_at >= start_date) \
            .group_by('year', 'month') \
            .order_by('year', 'month').all()

        labels = [f"{int(y)}-{int(m):02d}" for y, m in month_labels]

        statuses = ['Pending', 'Accepted', 'Rejected']
        status_data = {status: [] for status in statuses}
        for y, m in month_labels:
            for status in statuses:
                count = Application.query.filter(
                    extract('year', Application.applied_at) == y,
                    extract('month', Application.applied_at) == m,
                    Application.status == status
                ).count()
                status_data[status].append(count)

        companies = Company.query.all()
        company_status_data = {}
        for company in companies:
            company_status_data[company.name] = {status: [] for status in statuses}
            for y, m in month_labels:
                for status in statuses:
                    count = db.session.query(Application).join(Job).filter(
                        Job.company_id == company.id,
                        extract('year', Application.applied_at) == y,
                        extract('month', Application.applied_at) == m,
                        Application.status == status
                    ).count()
                    company_status_data[company.name][status].append(count)

        location_query = db.session.query(
            Job.location,
            func.count(Job.id)
        ).group_by(Job.location)

        if location_filter != 'all':
            location_query = location_query.filter(Job.location == location_filter)

        location_data = location_query.all()
        location_labels = [loc for loc, count in location_data]
        location_values = [count for loc, count in location_data]

        return self.render(
            'admin/report.html',
            total_users=total_users,
            total_candidates=total_candidates,
            total_companies=total_companies,
            total_jobs=total_jobs,
            total_applications=total_applications,
            total_approved_companies=total_approved_companies,
            labels=labels,
            status_data=status_data,
            company_status_data=company_status_data,
            months=months,
            all_locations=all_locations,
            location_filter=location_filter,
            location_labels=location_labels,
            location_values=location_values
        )

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin()


admin = Admin(app, name="Quản lý ApplyGO", template_mode="bootstrap4",
              url="/admin", index_view=MyAdminIndexView())

admin.add_view(UserView(User, db.session, name="Người dùng"))
admin.add_view(CompanyView(Company, db.session, name="Công ty", endpoint="company_admin"))
admin.add_view(CompanyApprovalView(Company, db.session, name="Kiểm duyệt Công ty", endpoint="company_approval"))
admin.add_view(JobView(Job, db.session, name="Tin tuyển dụng"))
admin.add_view(ApplicationView(Application, db.session, name="Ứng tuyển"))
admin.add_view(CandidateProfileView(CandidateProfile, db.session, name="Hồ sơ ứng viên"))
admin.add_view(ReportView(name="Báo cáo thống kê", endpoint="report"))
admin.add_view(LogoutView(name="Đăng xuất", endpoint="logout"))