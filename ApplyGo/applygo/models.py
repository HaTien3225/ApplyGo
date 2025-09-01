from datetime import datetime
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from applygo import db, app


# Enum trạng thái ứng tuyển
class ApplicationStatus(Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


# Bảng người dùng
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # candidate, company, admin

    # Quan hệ với CV hoặc Công ty
    candidate_profile = db.relationship("CandidateProfile", back_populates="user", uselist=False)
    company = db.relationship("Company", back_populates="user", uselist=False)

    def __str__(self):
        return self.username


# CV ứng viên
class CandidateProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    skills = db.Column(db.Text, nullable=True)
    experience = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="candidate_profile")
    applications = db.relationship("Application", back_populates="candidate_profile", cascade="all, delete-orphan")

    def __str__(self):
        return self.full_name


# Công ty
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", back_populates="company")
    jobs = db.relationship("Job", back_populates="company", cascade="all, delete-orphan")

    def __str__(self):
        return self.name


# Tin tuyển dụng
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    salary = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    company = db.relationship("Company", back_populates="jobs")
    applications = db.relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def __str__(self):
        return self.title


# Hồ sơ ứng tuyển
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    candidate_profile_id = db.Column(db.Integer, db.ForeignKey("candidate_profile.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    candidate_profile = db.relationship("CandidateProfile", back_populates="applications")
    job = db.relationship("Job", back_populates="applications")

    def __str__(self):
        return f"{self.candidate_profile.full_name} -> {self.job.title}"


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database created successfully!")
