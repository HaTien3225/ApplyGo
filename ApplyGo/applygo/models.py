from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from applygo import db, app


class UserRole(Enum):
    __table_args__ = {'extend_existing': True}
    CANDIDATE = "candidate"
    COMPANY = "company"
    ADMIN = "admin"


class ApplicationStatus(Enum):
    __table_args__ = {'extend_existing': True}
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


class JobStatus(Enum):
    __table_args__ = {'extend_existing': True}
    OPEN = "Open"
    CLOSED = "Closed"
    PAUSED = "Paused"


class CompanyStatus(Enum):
    __table_args__ = {'extend_existing': True}
    PENDING = "Pending"
    APPROVED = "Approved"
    DECLINED = "Declined"


class User(db.Model, UserMixin):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.CANDIDATE.value)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    image_url = db.Column(db.String(500), nullable=True)
    candidate_profile = db.relationship("CandidateProfile", back_ref="user", uselist=False, lazy=True)
    company = db.relationship("Company", back_populates="user", uselist=False)
    activities = db.relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == UserRole.ADMIN.value

    def is_candidate(self):
        return self.role == UserRole.CANDIDATE.value

    def is_company(self):
        return self.role == UserRole.COMPANY.value


class CandidateProfile(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)
    cv_template = db.Column(db.String(50), default='simple')
    uploaded_cv_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship("User", back_ref="candidate_profile", lazy=True)
    applications = db.relationship("Application", back_ref="candidate_profile", cascade="all, delete-orphan", lazy=True)

    def __str__(self):
        return self.full_name


class Company(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    logo_url = db.Column(db.String(500), nullable=True)
    mst = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=CompanyStatus.PENDING.value)
    user = db.relationship("User", back_ref="company", lazy=True)
    jobs = db.relationship("Job", back_ref="company", cascade="all, delete-orphan", lazy=True)

    def __str__(self):
        return self.name


class Job(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    salary = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=JobStatus.OPEN.value)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    category = db.relationship("Category", back_ref="jobs", lazy=True)
    company = db.relationship("Company", back_ref="jobs", lazy=True)
    applications = db.relationship("Application", back_ref="job", cascade="all, delete-orphan", lazy=True)

    def __str__(self):
        return f"{self.title} ({self.status})"

class Category(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    jobs = db.relationship("Job", back_ref="category", cascade="all, delete-orphan", lazy=True)

    def __str__(self):
        return self.name

class Application(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_profile_id = db.Column(db.Integer, db.ForeignKey("candidate_profile.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=ApplicationStatus.PENDING.value)
    applied_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    candidate_profile = db.relationship("CandidateProfile", back_ref="applications", lazy=True)
    job = db.relationship("Job", back_ref="applications", lazy=True)

    def __str__(self):
        return f"{self.candidate_profile.full_name} -> {self.job.title}"


class ActivityLog(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User", back_ref="activities", lazy=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"


class CvTemplate(db.Model):
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    html_file = db.Column(db.String(100), nullable=False)
    preview_image = db.Column(db.String(255), nullable=True)


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database created successfully!")
