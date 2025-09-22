from datetime import datetime, timedelta
from os import abort

from bs4 import BeautifulSoup
from flask import render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import extract
from unicodedata import category

from applygo import app, db, dao, login
from applygo.dao import get_jobs_by_company, upload_file_to_cloudinary, get_applications, get_my_applications, \
    get_all_cate
from applygo.decorators import loggedin, role_required
from applygo.models import User, Job, Application, CandidateProfile, CvTemplate, UserRole, JobStatus, Company, Category, \
    ApplicationStatus


import os
import math


@app.context_processor
def inject_user_roles():
    return dict(UserRole=UserRole)


@app.route('/')
def index():
    jobs = dao.get_all_jobs()[:5]
    companies = dao.get_companies()
    categories = dao.get_categories()
    return render_template('page/index.html', jobs=jobs, companies=companies, categories=categories)


@app.route("/login-admin/", methods=["GET", "POST"])
def login_admin():
    err_msg = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = dao.auth_user(username=username, password=password)
        if user and user.is_admin():
            login_user(user)
            return redirect('/admin/')
        else:
            err_msg = "Sai tên đăng nhập hoặc không có quyền truy cập Admin."
    return render_template("auth/login_admin.html", err_msg=err_msg)


@loggedin
@app.route('/login/', methods=['GET', 'POST'])
def login_my_user():
    err_msg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username=username, password=password)
        if not user:
            err_msg = 'Tên đăng nhập hoặc mật khẩu không đúng!'
            return render_template('auth/login.html', err_msg=err_msg)

        if user.is_candidate() or user.is_company():
            login_user(user)
        elif user.is_admin():
            login_user(user)
            return redirect('/admin/')
        else:
            err_msg = 'Người dùng không có vai trò hợp lệ!'
            return render_template('auth/login.html', err_msg=err_msg)

        next_url = request.args.get('next')
        if not next_url or not next_url.startswith('/'):
            next_url = '/'
        return redirect(next_url)

    return render_template('auth/login.html', err_msg=err_msg)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    err_msg = None
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            err_msg = "Mật khẩu xác nhận không khớp!"
        if User.query.filter_by(username=username).first():
            err_msg = "Tên đăng nhập đã tồn tại!"
            return render_template('auth/register.html', err_msg=err_msg)
        if User.query.filter_by(email=email).first():
            err_msg = "Email đã tồn tại!"
            return render_template('auth/register.html', err_msg=err_msg)
        try:
            dao.create_user(name=name, username=username, password=password, email=email, role="candidate")
            return redirect('/login/')
        except Exception as ex:
            db.session.rollback()
            err_msg = f"Lỗi đăng ký: {str(ex)}"

    return render_template('auth/register.html', err_msg=err_msg)


@app.route('/logout/')
@login_required
def logout_user_route():
    logout_user()
    return redirect('/')


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(int(user_id))


@app.route('/edit-recruitment-post/<int:id>/', methods=['POST'])
@login_required
@role_required(UserRole.COMPANY.value)
def edit_recruitment_post(id):
    job = Job.query.get_or_404(id)
    if job.company_id != current_user.company.id:
        flash("Bạn không có quyền chỉnh sửa tin tuyển dụng này", "danger")
        return redirect(url_for('recruitment_post_manager'))

    title = request.form.get('title', '').strip()
    salary = request.form.get('salary', '').strip()
    description = request.form.get('description', '').strip()
    location = request.form.get('location', '').strip()
    status = request.form.get('status', '').strip()
    requirement = request.form.get('requirement', '').strip()
    cate_id = int(request.form.get('cate_id', '').strip())

    def clean_html(text):
        return BeautifulSoup(text, "html.parser").get_text()

    title = clean_html(title)
    description = clean_html(description)
    location = clean_html(location)
    requirement = clean_html(requirement)

    if cate_id == -1:
        flash("Hãy chọn doanh mục", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    if Category.query.filter_by(id=cate_id).first() == None:
        flash("Hãy chọn doanh mục", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    if not title:
        flash("Chưa nhập tiêu đề tin tuyển dụng", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))
    elif len(title) > 200:
        flash("Tiêu đề không được vượt quá 200 ký tự", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    if not requirement:
        flash("Chưa nhập yêu cầu tin tuyển dụng", "danger")
        return redirect(url_for('create_recruitment_post'))
    elif len(requirement) > 5000:
        flash("Yêu cầu không được vượt quá 5000 ký tự", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    if not salary:
        flash("Chưa nhập mức lương", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))
    elif len(salary) > 20:
        flash("Mức lương quá dài", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    if not description:
        flash("Chưa nhập mô tả công việc", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))
    elif len(description) > 5000:
        flash("Mô tả công việc không được vượt quá 5000 ký tự", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    if not location:
        flash("Chưa nhập nơi làm việc", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))
    elif len(location) > 100:
        flash("Nơi làm việc không được vượt quá 100 ký tự", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    if status not in ["Open", "Closed", "Paused"]:
        flash("Trạng thái không hợp lệ", "danger")
        return redirect(url_for('edit_recruitment_post', id=id))

    job.title = title
    job.salary = salary
    job.description = description
    job.location = location
    job.status = status
    job.requirements = requirement
    job.category_id = cate_id
    db.session.commit()

    flash("Cập nhật tin tuyển dụng thành công!", "success")
    return redirect(url_for('recruitment_post_detail', id=id))


@app.route('/recruitment-post-detail/<int:id>/', methods=['GET'])
@login_required
@role_required(UserRole.COMPANY.value)
def recruitment_post_detail(id):
    job = Job.query.get_or_404(id)
    cates = get_all_cate()

    status = request.args.get("status")
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
    except ValueError:
        page, page_size = 1, 10


    result = get_applications(job_id=id, status=status, page=page, page_size=page_size)
    applications = result["applications"]
    total_pages = result["total_pages"]

    return render_template(
        'company/edit_recruitment_post.html',
        job=job,
        applications=applications,
        total_pages=total_pages,
        current_page=page,
        current_status=status,
        categorys = cates
    )


@app.route('/recruitment-post-manager/<int:id>/delete/', methods=['POST'])
@login_required
@role_required(UserRole.COMPANY.value)
def delete_recruitment_post(id):
    job = Job.query.get_or_404(id)

    if job.company_id != current_user.company.id:
        flash("Bạn không có quyền xóa tin tuyển dụng này", "danger")
        return redirect(url_for('recruitment_post_manager'))

    db.session.delete(job)
    db.session.commit()
    flash("Xóa tin tuyển dụng thành công!", "success")
    return redirect(url_for('recruitment_post_manager'))


@app.route('/recruitment-post-manager/')
@role_required(UserRole.COMPANY.value)
def recruitment_post_manager():
    sort = request.args.get('sort')
    kw = request.args.get('kw')
    page = int(request.args.get('page', 1))
    status = request.args.get('status')
    page_size = 12
    company = current_user.company
    total_jobs = Job.query.filter(Job.company_id == company.id).count()
    if page >= math.ceil(total_jobs / page_size):
        page = 1
    sort_by = False
    if sort == 'desc':
        sort_by = False
    else:
        sort_by = True
    Jstatus = None
    if status == "OPEN":
        Jstatus = JobStatus.OPEN.value
    if status == "CLOSED":
        Jstatus = JobStatus.CLOSED.value
    if status == "PAUSED":
        Jstatus = JobStatus.PAUSED.value

    jobs, total = get_jobs_by_company(company_id=company.id, sort_by_date_incr=sort_by, page_size=12, page=page, kw=kw,
                                      status=Jstatus)
    # print(jobs[6].category.name)
    return render_template('company/recruitment_post_manager.html', company_jobs=jobs, page=page)


@app.route('/recruitment-post/create/', methods=['POST', 'GET'])
@role_required(UserRole.COMPANY.value)
def create_recruitment_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        salary = request.form.get('salary', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        requirement = request.form.get('requirement', '').strip()
        cate_id = int (request.form.get('cate_id', '').strip())

        def clean_html(text):
            soup = BeautifulSoup(text, "html.parser")
            return soup.get_text()

        title = clean_html(title)
        description = clean_html(description)
        location = clean_html(location)
        requirement = clean_html(requirement)
        if cate_id == -1:
            flash("Hãy chọn doanh mục", "danger")
            return redirect(url_for('create_recruitment_post'))

        if Category.query.filter_by(id=cate_id).first() == None:
            flash("Hãy chọn doanh mục", "danger")
            return redirect(url_for('create_recruitment_post'))

        if not title:
            flash("Chưa nhập tiêu đề tin tuyển dụng", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())
        elif len(title) > 200:
            flash("Tiêu đề không được vượt quá 200 ký tự", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())

        if not requirement:
            flash("Chưa nhập yêu cầu tin tuyển dụng", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())
        elif len(requirement) > 5000:
            flash("Yêu cầu không được vượt quá 5000 ký tự", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())

        if not salary:
            flash("Chưa nhập mức lương", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())
        elif len(salary) > 20:
            flash("Mức lương quá dài", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())
        if not description:
            flash("Chưa nhập mô tả công việc", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())
        elif len(description) > 5000:
            flash("Mô tả công việc không được vượt quá 5000 ký tự", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())

        if not location:
            flash("Chưa nhập nơi làm việc", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())
        elif len(location) > 100:
            flash("Nơi làm việc không được vượt quá 100 ký tự", "danger")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement,o_cate=Category.query.filter_by(id=cate_id).first())


        try:
            job = Job(
                company_id=current_user.company.id,
                title=title,
                salary=salary,
                description=description,
                location=location,
                requirements=requirement,
                category_id=cate_id,
            )
            db.session.add(job)
            db.session.commit()
        except:
            flash("Lỗi khi tạo đơn đăng tuyển", "warning")
            return render_template('company/create_recruitment_post.html',title=title,salary=salary,description=description,location=location,requirement=requirement)

        flash("Tạo tin tuyển dụng thành công!", "success")
        return redirect(url_for('recruitment_post_manager'))

    cates = get_all_cate()

    return render_template('company/create_recruitment_post.html',categorys=cates)

@app.route('/application/<int:id>/detail', methods=['GET'])
@login_required
@role_required(UserRole.COMPANY.value)
def application_detail(id):
    application = Application.query.get_or_404(id)
    profile = application.candidate_profile


    template_name = profile.cv_template or 'simple'
    template_path = f'company/cv_templates/{template_name}.html'

    return render_template(template_path, profile=profile, application=application)


@app.route('/application/<int:id>/update-status', methods=['POST'])
@login_required
@role_required(UserRole.COMPANY.value)
def update_application_status(id):
    application = Application.query.get_or_404(id)

    new_status = request.form.get('status')
    if new_status not in ['Accepted', 'Rejected']:
        flash("Trạng thái không hợp lệ!", "danger")
        return redirect(request.referrer or url_for('index'))

    application.status = new_status
    application.updated_at = datetime.now()
    db.session.commit()

    flash(f"Đã cập nhật trạng thái thành {new_status}", "success")
    return redirect(request.referrer or url_for('recruitment_post_detail', id=application.job_id))



@app.route('/jobs/<int:job_id>/')
def job_detail(job_id):
    job = dao.get_job_by_id(job_id)
    if not job:
        flash("Tin tuyển dụng không tồn tại!", "warning")
        return redirect(url_for('jobs'))
    similar_jobs = Job.query.filter(
        Job.location == job.location,
        Job.category==job.category,
        Job.id != job.id
    ).limit(5).all()

    return render_template('candidate/job_detail.html', job=job, similar_jobs=similar_jobs)


@app.route('/apply/<int:job_id>/', methods=['POST'])
@login_required
@role_required(UserRole.CANDIDATE.value)
def apply_job(job_id):
    try:
        dao.apply_job(user_id=current_user.id, job_id=job_id)
        flash("Ứng tuyển thành công!", "success")
    except Exception as e:
        flash(f"Lỗi ứng tuyển: {str(e)}", "danger")
    return redirect(url_for('job_detail', job_id=job_id))


@app.route('/applications/')
@login_required
def applications():
    apps = dao.get_applications_by_user(current_user.id)
    return render_template('applications.html', applications=apps)


@app.route("/candidate/cv/create/", methods=["GET", "POST"])
@login_required
def create_cv():
    if not current_user.is_candidate():
        flash("Chỉ ứng viên mới có thể tạo CV!", "danger")
        return redirect(url_for("index"))

    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()

    if request.method == "POST":
        full_name = request.form.get("full_name")
        phone = request.form.get("phone")
        skills = request.form.get("skills")
        experience = request.form.get("experience")
        education = request.form.get("education")

        if profile:
            profile.full_name = full_name
            profile.phone = phone
            profile.skills = skills
            profile.experience = experience
            profile.education = education
        else:
            profile = CandidateProfile(
                user_id=current_user.id,
                full_name=full_name,
                phone=phone,
                skills=skills,
                experience=experience,
                education=education
            )
            db.session.add(profile)

        try:
            db.session.commit()
            flash("CV của bạn đã được lưu!", "success")
            return redirect(url_for("view_cv"))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi lưu CV: {str(e)}", "danger")

    return render_template("candidate/create_cv.html", profile=profile)


@app.route("/candidate/cv/view/")
@login_required
def view_cv():
    if not current_user.is_candidate():
        flash("Chỉ ứng viên mới có thể xem CV!", "danger")
        return redirect(url_for("index"))

    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()

    if not profile or not profile.cv_template:
        flash("Bạn chưa tạo CV hoặc chưa chọn mẫu. Vui lòng tạo và chọn mẫu CV để xem.", "warning")
        return redirect(url_for("create_cv"))

    template_file = f"candidate/cv_templates/{profile.cv_template}.html"
    return render_template(template_file, profile=profile)


@app.route('/candidate/cv/select_template/', methods=['GET', 'POST'])
@login_required
def select_cv_template():
    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()
    templates = CvTemplate.query.all()

    if request.method == 'POST':
        template_id = request.form.get('template_id', type=int)

        if not profile:
            profile = CandidateProfile(user_id=current_user.id)
            db.session.add(profile)
            db.session.commit()

        selected_template = CvTemplate.query.get(template_id)
        if selected_template:
            profile.cv_template = selected_template.html_file
            db.session.commit()
            flash(f"Mẫu CV '{selected_template.name}' đã được chọn. Bây giờ bạn có thể chỉnh sửa thông tin CV.",
                  "success")
            return redirect(url_for('view_cv'))
        else:
            flash("Mẫu CV không hợp lệ.", "danger")
            return redirect(url_for('select_cv_template'))

    return render_template('candidate/select_template.html', templates=templates, profile=profile)


@app.route("/candidate/cv/preview/<template_name>/")
@login_required
def preview_cv(template_name):
    fake_profile = CandidateProfile(
        full_name="Nguyễn Văn A",
        phone="0123456789",
        skills="Kỹ năng 1, Kỹ năng 2, Kỹ năng 3",
        experience="Kinh nghiệm làm việc",
        education="Thông tin học vấn"
    )

    template = CvTemplate.query.filter_by(html_file=template_name).first()
    if not template:
        return "Mẫu CV không tồn tại", 404

    return render_template(f"candidate/cv_templates/{template.html_file}.html", profile=fake_profile)


@app.route("/candidate/cv/manage/")
@login_required
def manage_cv():
    if not current_user.is_candidate():
        flash("Chỉ ứng viên mới có thể quản lý CV.", "danger")
        return redirect(url_for("index"))

    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()
    return render_template("candidate/manage_cv.html", profile=profile)


# Allowed extensions: include images for logos
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/candidate/cv/upload/", methods=["GET", "POST"])
@login_required
def upload_cv():
    if not current_user.is_candidate():
        flash("Chỉ ứng viên mới có thể tải CV lên.", "danger")
        return redirect(url_for("index"))

    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash("Bạn cần tạo hồ sơ trước khi tải CV lên.", "warning")
        return redirect(url_for("create_cv"))

    if request.method == "POST":
        if 'cv_file' not in request.files:
            flash("Không có file được chọn.", "danger")
            return redirect(request.url)

        file = request.files['cv_file']

        if file.filename == '':
            flash("Không có file nào được tải lên.", "warning")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                # upload to Cloudinary (resource_type='auto' supports pdf/docx)
                cv_url = upload_file_to_cloudinary(file, folder='applygo/cvs')

                # If previously had a local file path, try to remove it
                if profile.uploaded_cv_path and profile.uploaded_cv_path.startswith('/static/uploads'):
                    try:
                        old_path = os.path.join(app.static_folder, profile.uploaded_cv_path.replace('/static/', ''))
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    except Exception:
                        pass

                profile.uploaded_cv_path = cv_url
                db.session.commit()

                flash("CV của bạn đã được tải lên Cloudinary!", "success")
                return redirect(url_for("manage_cv"))

            except Exception as e:
                db.session.rollback()
                flash(f"Lỗi khi tải CV: {str(e)}", "danger")
                return redirect(request.url)
        else:
            flash("Định dạng file không được hỗ trợ. Vui lòng tải lên file PDF hoặc DOCX.", "warning")
            return redirect(request.url)

    return render_template("candidate/upload_cv.html", profile=profile)


@app.route("/candidate/cv/download/<filename>/")
@login_required
def serve_uploaded_cv(filename):
    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()
    if profile and profile.uploaded_cv_path == filename:
        # if stored as URL, redirect
        if profile.uploaded_cv_path.startswith('http'):
            return redirect(profile.uploaded_cv_path)
        return send_from_directory(os.path.join(app.static_folder, 'uploads'), filename, as_attachment=True)
    return "File không tồn tại hoặc bạn không có quyền truy cập.", 404


@app.route("/candidate/cv/download/")
@login_required
def download_cv_latest():
    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()
    if not profile or not profile.uploaded_cv_path:
        return "Bạn chưa có CV.", 404

    if profile.uploaded_cv_path.startswith("http"):
        return redirect(profile.uploaded_cv_path)
    return send_from_directory(os.path.join(app.static_folder, 'uploads'), profile.uploaded_cv_path, as_attachment=True)


@app.route('/candidate/profile/', methods=['GET', 'POST'])
@login_required
def candidate_profile():
    if not current_user.is_candidate():
        flash("Bạn không có quyền truy cập trang này!", "danger")
        return redirect(url_for('index'))

    profile = current_user.candidate_profile
    if not profile:
        flash("Bạn chưa tạo hồ sơ. Vui lòng tạo CV trước!", "warning")
        return redirect(url_for('create_cv'))

    try:
        months = int(request.args.get('months', 6))
    except ValueError:
        months = 6

    status_filter = request.args.get('status_filter', 'all')

    total_applications = Application.query.filter_by(candidate_profile_id=profile.id).count()

    statuses = ["Pending", "Accepted", "Rejected"]
    applications_status_count = {
        status: Application.query.filter_by(candidate_profile_id=profile.id, status=status).count()
        for status in statuses
    }

    now = datetime.now()
    start_date = datetime.min if months == 0 else now - timedelta(days=30 * months)

    month_labels_query = db.session.query(
        extract('year', Application.applied_at).label('year'),
        extract('month', Application.applied_at).label('month')
    ).filter(
        Application.candidate_profile_id == profile.id,
        Application.applied_at >= start_date
    ).group_by('year', 'month').order_by('year', 'month').all()

    labels = [f"{int(y)}-{int(m):02d}" for y, m in month_labels_query]

    chart_data = {status: [] for status in statuses}
    for y, m in month_labels_query:
        for status in statuses:
            count = Application.query.filter(
                Application.candidate_profile_id == profile.id,
                extract('year', Application.applied_at) == y,
                extract('month', Application.applied_at) == m,
                Application.status == status
            ).count()
            chart_data[status].append(count)

    return render_template(
        'profile/candidate_profile.html',
        profile=profile,
        total_applications=total_applications,
        applications_status_count=applications_status_count,
        labels=labels,
        chart_data=chart_data,
        months=months,
        status_filter=status_filter
    )


@app.route('/company/profile/', methods=['GET', 'POST'])
@login_required
def company_profile():
    if not current_user.is_company():
        flash("Bạn không có quyền truy cập trang này!", "danger")
        return redirect(url_for('index'))

    company = current_user.company

    if request.method == "POST":
        company.name = request.form.get("name")
        company.address = request.form.get("address")
        company.website = request.form.get("website")
        company.mst = request.form.get("mst")
        logo_file = request.files.get("logo")
        if logo_file and allowed_file(logo_file.filename):
            try:
                # upload logo to Cloudinary
                logo_url = upload_file_to_cloudinary(logo_file, folder='applygo/company_logos')
                company.logo_url = logo_url
            except Exception as e:
                flash(f"Lỗi khi lưu logo: {str(e)}", "warning")
        db.session.commit()
        flash("Cập nhật thông tin công ty thành công!", "success")
        return redirect(url_for('company_profile'))

    try:
        months = int(request.args.get("months", 6))
    except:
        months = 6
    status = request.args.get("status", "all")

    now = datetime.now()
    if months > 0:
        start_date = now - timedelta(days=30 * months)
    else:
        start_date = datetime(2000, 1, 1)

    # Application does not have company_id: join via Job
    month_labels_query = db.session.query(
        extract('year', Application.applied_at).label('year'),
        extract('month', Application.applied_at).label('month')
    ).join(Job, Application.job_id == Job.id).filter(
        Job.company_id == company.id,
        Application.applied_at >= start_date
    )
    if status != "all":
        month_labels_query = month_labels_query.filter(Application.status == status)

    month_labels = month_labels_query.group_by('year', 'month').order_by('year', 'month').all()
    labels = [f"{int(y)}-{int(m):02d}" for y, m in month_labels]

    statuses = ["Pending", "Accepted", "Rejected"]
    chart_data = {s: [] for s in statuses}

    for y, m in month_labels:
        for s in statuses:
            if status != "all" and s != status:
                chart_data[s].append(0)
            else:
                count = db.session.query(Application).join(Job, Application.job_id == Job.id).filter(
                    Job.company_id == company.id,
                    extract('year', Application.applied_at) == y,
                    extract('month', Application.applied_at) == m,
                    Application.status == s
                ).count()
                chart_data[s].append(count)

    return render_template(
        'profile/company_profile.html',
        company=company,
        labels=labels,
        chart_data=chart_data,
        months=months,
        status=status
    )


@app.route("/jobs/")
def jobs():
    page = request.args.get("page", 1, type=int)
    kw = request.args.get("kw", "")
    company_id = request.args.get("company_id", type=int)
    status = request.args.get("status", "")
    salary_range = request.args.get("salary_range", "")
    location = request.args.get("location", "")
    posted = request.args.get("posted", "")
    category_id = request.args.get("category_id", type=int)

    query = Job.query

    # Lọc theo từ khóa
    if kw:
        query = query.filter(Job.title.ilike(f"%{kw}%"))

    # Lọc theo công ty
    if company_id:
        query = query.filter(Job.company_id == company_id)

    # Lọc theo trạng thái
    if status:
        query = query.filter(Job.status == status)

    # Lọc theo khoảng lương
    if salary_range:
        try:
            min_salary, max_salary = map(int, salary_range.split("-"))
            query = query.filter(Job.salary >= min_salary, Job.salary <= max_salary)
        except:
            pass

    # Lọc theo địa điểm
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    # Lọc theo ngày đăng
    if posted:
        days = int(posted)
        cutoff = datetime.now() - timedelta(days=days)
        query = query.filter(Job.created_at >= cutoff)

    if category_id:
        query = query.filter(Job.category_id == category_id)

    # Phân trang
    page_size = app.config["PAGE_SIZE"]
    jobs = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)

    companies = Company.query.all()
    categories = Category.query.all()

    return render_template(
        "candidate/jobs.html",
        jobs=jobs.items,
        total=jobs.total,
        page=page,
        page_size=page_size,
        companies=companies,
        kw=kw,
        company_id=company_id,
        status=status,
        salary_range=salary_range,
        location=location,
        posted=posted,
        categories=categories,
        category_id=category_id
    )


@app.route("/applications/my", methods=["GET"])
@login_required
def my_applications():
    if current_user.role.lower() != "candidate":
        return "Only candidates can view applications", 403

    apps = get_my_applications(current_user.candidate_profile.id)
    return render_template("candidate/my_applications.html", applications=apps)


@app.route("/candidate/applications/<int:app_id>")
@login_required
def candidate_application_detail(app_id):
    app_obj = Application.query.get_or_404(app_id)

    # chỉ cho phép đúng candidate xem
    if app_obj.candidate_profile.user_id != current_user.id:
        abort(403)

    return render_template("candidate/application_detail.html", application=app_obj)

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=False)
