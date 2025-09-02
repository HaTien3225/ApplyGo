from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from applygo import app, db, dao, login
from applygo.decorators import loggedin
from applygo.models import User, Job, Company, Application, CandidateProfile, CvTemplate
# Cần thêm imports ở đầu file nếu chưa có
from werkzeug.utils import secure_filename
import os
base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

# ------------------------
# TRANG CHỦ
# ------------------------
@app.context_processor
def inject_user_roles():
    return dict(UserRole=UserRole)

@app.route('/')
def index():
    jobs = dao.get_all_jobs()[:10]  # 10 việc mới nhất
    companies = dao.get_companies()
    return render_template('page/index.html', jobs=jobs, companies=companies)


# ------------------------
# AUTH
# ------------------------

# Route login admin
# ----------------------------
@app.route("/login-admin/", methods=["GET", "POST"])
def login_admin():
    err_msg = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = dao.auth_user(username=username, password=password)
        if user and user.is_admin():  # bạn có thể hash password
            login_user(user)
            return redirect('/admin')
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

        # Kiểm tra role và login
        if user.is_candidate() or user.is_company():
            login_user(user)
        elif user.is_admin():
            login_user(user)
            return redirect('/admin/')
        else:
            err_msg = 'Người dùng không có vai trò hợp lệ!'
            return render_template('auth/login.html', err_msg=err_msg)

        # Điều hướng sau khi login
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
        phone = request.form.get('phone')
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
            dao.create_user(name=name, username=username, password=password, email=email, phone=phone, role="candidate")
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


# ------------------------
# JOBS
# ------------------------
@app.route('/jobs/')
def jobs():
    keyword = request.args.get('keyword')
    company_id = request.args.get('company_id', type=int)
    jobs = dao.search_jobs(keyword=keyword, company_id=company_id)
    companies = dao.get_companies()
    return render_template('jobs.html', jobs=jobs, companies=companies)

@app.route('/recruitment-post-manager/')
@role_required(UserRole.COMPANY)
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
     # 'asc' hoặc 'desc'
    sort_by = False
    if sort == 'desc':
        sort_by = False
    else:
        sort_by = True
    Jstatus = None
    if status == "OPEN":
        Jstatus = JobStatus.OPEN
    if status == "CLOSED":
        Jstatus = JobStatus.CLOSED
    if status == "PAUSED":
        Jstatus = JobStatus.PAUSED

    jobs , total = get_jobs_by_company(company_id=company.id,sort_by_date_incr=sort_by,page_size=12,page=page,kw=kw,status=Jstatus)
    print(total_jobs)
    # print(jobs[0].title)
    return render_template('company/recruitment_post_manager.html',company_jobs=jobs,page=page)



@app.route('/jobs/<int:job_id>/')
def job_detail(job_id):
    job = dao.get_job_by_id(job_id)
    if not job:
        flash("Tin tuyển dụng không tồn tại!", "warning")
        return redirect(url_for('jobs'))
    return render_template('job_detail.html', job=job)


# ------------------------
# APPLY
# ------------------------
@app.route('/apply/<int:job_id>/', methods=['POST'])
@login_required
def apply_job(job_id):
    try:
        dao.apply_job(user_id=current_user.id, job_id=job_id)
        flash("Ứng tuyển thành công!", "success")
    except Exception as e:
        flash(f"Lỗi ứng tuyển: {str(e)}", "danger")
    return redirect(url_for('job_detail', job_id=job_id))


# ------------------------
# APPLICATIONS
# ------------------------
@app.route('/applications/')
@login_required
def applications():
    apps = dao.get_applications_by_user(current_user.id)
    return render_template('applications.html', applications=apps)

@app.route("/candidate/cv/create", methods=["GET", "POST"])
@login_required
def create_cv():
    # kiểm tra user có phải candidate không
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


        if profile:  # update nếu đã có CV
            profile.full_name = full_name
            profile.phone = phone
            profile.skills = skills
            profile.experience = experience
            profile.education = education
        else:  # tạo mới
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
            # Dòng này đã được thay đổi
            return redirect(url_for("view_cv"))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi khi lưu CV: {str(e)}", "danger")

    return render_template("candidate/create_cv.html", profile=profile)


@app.route("/candidate/cv/view")
@login_required
def view_cv():
    if not current_user.is_candidate():
        flash("Chỉ ứng viên mới có thể xem CV!", "danger")
        return redirect(url_for("index"))

    # Lấy hồ sơ của người dùng hiện tại
    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()

    if not profile or not profile.cv_template:
        flash("Bạn chưa tạo CV hoặc chưa chọn mẫu. Vui lòng tạo và chọn mẫu CV để xem.", "warning")
        return redirect(url_for("create_cv"))

    template_file = f"candidate/cv_templates/{profile.cv_template}.html"
    return render_template(template_file, profile=profile)


@app.route('/candidate/cv/select_template', methods=['GET', 'POST'])
@login_required
def select_cv_template():
    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()
    templates = CvTemplate.query.all()

    if request.method == 'POST':
        template_id = request.form.get('template_id', type=int)

        if not profile:
            # Nếu người dùng chưa có profile, tạo một profile rỗng
            profile = CandidateProfile(user_id=current_user.id)
            db.session.add(profile)
            db.session.commit()

        selected_template = CvTemplate.query.get(template_id)
        if selected_template:
            profile.cv_template = selected_template.html_file
            db.session.commit()
            flash(f"Mẫu CV '{selected_template.name}' đã được chọn. Bây giờ bạn có thể chỉnh sửa thông tin CV.", "success")
            # Dòng này đã được thay đổi để chuyển đến trang xem
            return redirect(url_for('view_cv'))
        else:
            flash("Mẫu CV không hợp lệ.", "danger")
            return redirect(url_for('select_cv_template'))

    return render_template('candidate/select_template.html', templates=templates, profile=profile)


@app.route("/candidate/cv/preview/<template_name>")
@login_required
def preview_cv(template_name):
    # Luôn sử dụng dữ liệu giả để xem trước
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


@app.route("/candidate/cv/manage")
@login_required
def manage_cv():
    # Kiểm tra quyền truy cập
    if not current_user.is_candidate():
        flash("Chỉ ứng viên mới có thể quản lý CV.", "danger")
        return redirect(url_for("index"))

    # Lấy hồ sơ của ứng viên hiện tại
    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()

    # Render template mới và truyền dữ liệu hồ sơ vào
    return render_template("candidate/manage_cv.html", profile=profile)


# Cấu hình thư mục tải lên
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'cvs')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route("/candidate/cv/upload", methods=["GET", "POST"])
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
                # Tạo tên file an toàn và duy nhất
                filename = secure_filename(file.filename)
                # Đổi tên file để tránh trùng lặp
                file_ext = filename.rsplit('.', 1)[1]
                unique_filename = f"{current_user.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                # Xóa file CV cũ nếu tồn tại
                if profile.uploaded_cv_path:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.uploaded_cv_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                # Lưu file mới
                file.save(file_path)

                # Cập nhật đường dẫn file vào cơ sở dữ liệu
                profile.uploaded_cv_path = unique_filename
                db.session.commit()

                flash("CV của bạn đã được tải lên thành công!", "success")
                return redirect(url_for("manage_cv"))

            except Exception as e:
                db.session.rollback()
                flash(f"Lỗi khi tải CV: {str(e)}", "danger")
                return redirect(request.url)
        else:
            flash("Định dạng file không được hỗ trợ. Vui lòng tải lên file PDF hoặc DOCX.", "warning")
            return redirect(request.url)

    return render_template("candidate/upload_cv.html", profile=profile)


@app.route("/candidate/cv/download/<filename>")
@login_required
def serve_uploaded_cv(filename):
    # Kiểm tra xem file có thuộc về người dùng hiện tại không
    profile = CandidateProfile.query.filter_by(user_id=current_user.id).first()
    if profile and profile.uploaded_cv_path == filename:
        # Phục vụ file từ thư mục đã cấu hình
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    # Trả về lỗi 404 nếu file không tồn tại hoặc không thuộc về người dùng
    return "File không tồn tại hoặc bạn không có quyền truy cập.", 404

if __name__ == "__main__":
    with app.app_context():
        # In ra tất cả các route đang có
        print("Danh sách route hiện tại:")
        for rule in app.url_map.iter_rules():
            print(f"{rule} -> {rule.endpoint} (methods: {','.join(rule.methods)})")

        # Kiểm tra nhanh /admin/
        admin_routes = [rule for rule in app.url_map.iter_rules() if "/admin" in rule.rule]
        if admin_routes:
            print("\nCác route liên quan đến /admin/:")
            for r in admin_routes:
                print(f"{r} -> {r.endpoint}")
        else:
            print("\nChưa có route /admin/ nào được đăng ký!")

        app.run(debug=False)
