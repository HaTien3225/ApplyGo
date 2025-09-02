import hashlib
from datetime import datetime

from sqlalchemy.orm import Query

from applygo import app, db
from applygo.models import User, CandidateProfile, Company, Job, Application, ApplicationStatus, JobStatus


# ------------------------
# AUTH & USER
# ------------------------

def hash_password(password: str) -> str:
    """Mã hóa mật khẩu bằng MD5 (tạm, có thể nâng cấp sang bcrypt sau)"""
    return hashlib.md5(password.strip().encode("utf-8")).hexdigest()


def auth_user(username: str, password: str):
    """Xác thực user khi login"""
    hashed = hash_password(password)
    return User.query.filter_by(
        username=username.strip(),
        password=hashed
    ).first()


def get_user_by_id(user_id: int):
    return User.query.get(user_id)


def get_user_role(user: User):
    """Trả về role của user: candidate / company / admin"""
    if not user:
        return None
    return user.role.lower()


def create_user(name, username, password, email, phone, role="candidate"):
    """Đăng ký user mới (ứng viên mặc định)"""
    hashed_password = hash_password(password)

    user = User(
        username=username.strip(),
        password=hashed_password,
        email=email.strip(),
        phone=phone.strip(),
        role=role.lower()
    )
    db.session.add(user)
    db.session.flush()  # để có user.id ngay

    # Tạo profile hoặc công ty tương ứng
    if role.lower() == "candidate":
        profile = CandidateProfile(user_id=user.id, full_name=name.strip())
        db.session.add(profile)
    elif role.lower() == "company":
        company = Company(user_id=user.id, name=name.strip())
        db.session.add(company)

    db.session.commit()
    return user


# ------------------------
# JOB & COMPANY
# ------------------------

def get_all_jobs():
    return Job.query.order_by(Job.created_at.desc()).all()


def get_job_by_id(job_id: int):
    return Job.query.get(job_id)


def search_jobs(keyword=None, company_id=None):
    query = Job.query
    if keyword:
        query = query.filter(Job.title.ilike(f"%{keyword.strip()}%"))
    if company_id:
        query = query.filter(Job.company_id == company_id)
    return query.order_by(Job.created_at.desc()).all()


def get_companies():
    return Company.query.all()


def get_company_by_id(company_id: int):
    return Company.query.get(company_id)


# ------------------------
# APPLICATION
# ------------------------

def apply_job(user_id: int, job_id: int):
    """Ứng viên nộp đơn ứng tuyển"""
    user = User.query.get(user_id)
    if not user or not user.candidate_profile:
        raise ValueError("Chỉ ứng viên mới có thể ứng tuyển!")

    candidate_profile_id = user.candidate_profile.id

    # Kiểm tra ứng tuyển trùng
    existing = Application.query.filter_by(
        candidate_profile_id=candidate_profile_id,
        job_id=job_id
    ).first()
    if existing:
        raise ValueError("Bạn đã ứng tuyển công việc này rồi!")

    application = Application(
        candidate_profile_id=candidate_profile_id,
        job_id=job_id,
        status=ApplicationStatus.PENDING,
        applied_at=datetime.utcnow()
    )
    db.session.add(application)
    db.session.commit()
    return application


def get_applications_by_user(user_id: int):
    user = User.query.get(user_id)
    if not user or not user.candidate_profile:
        return []
    return Application.query.filter_by(
        candidate_profile_id=user.candidate_profile.id
    ).order_by(Application.applied_at.desc()).all()


def get_applications_by_company(company_id: int):
    return Application.query.join(Job).filter(Job.company_id == company_id).order_by(Application.applied_at.desc()).all()


# ------------------------
# ADMIN / REPORT
# ------------------------
def get_jobs_by_company(company_id, page=1, page_size=10, kw=None, sort_by_date_incr=False, status=None):

    query: Query = Job.query.filter(Job.company_id == company_id)

    # filter theo status
    if status is not None:
        query = query.filter(Job.status == status)

    # filter theo từ khóa
    if kw:
        query = query.filter(Job.title.ilike(f"%{kw}%"))

    # sort
    if sort_by_date_incr:
        query = query.order_by(Job.created_at.asc())
    else:
        query = query.order_by(Job.created_at.desc())

    # tổng số record
    total = query.count()

    # phân trang
    jobs = query.offset((page - 1) * page_size).limit(page_size).all()

    return jobs, total

def get_job_statistics():
    """Thống kê số lượng ứng tuyển theo công việc"""
    return db.session.query(
        Job.title,
        db.func.count(Application.id).label("applications")
    ).join(Application, Application.job_id == Job.id, isouter=True)\
     .group_by(Job.id).all()


# ------------------------
# TEST DAO
# ------------------------
if __name__ == "__main__":
    with app.app_context():
        # print("Jobs:", get_all_jobs())
        # print("Companies:", get_companies())
        admin_user = User(username='admin', password=hash_password('admin123'),email='admin@gmail.com', is_admin=True)
        db.session.add(admin_user)
        db.session.commit()


