from datetime import datetime
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from applygo import app, db, dao, login
from applygo.decorators import loggedin
from applygo.models import User, Job, Company, Application


# ------------------------
# TRANG CHỦ
# ------------------------
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

        app.run(debug=True)
