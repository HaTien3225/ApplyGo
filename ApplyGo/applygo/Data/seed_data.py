from applygo import db, app
from applygo.models import User, CandidateProfile, Company, Job, Application, ApplicationStatus
import hashlib
from datetime import datetime


def seed_data():
    try:
        # Xóa dữ liệu cũ
        db.session.query(Application).delete()
        db.session.query(Job).delete()
        db.session.query(Company).delete()
        db.session.query(CandidateProfile).delete()
        db.session.query(User).delete()

        # --- Tạo Users ---
        admin = User(
            username="admin",
            email="admin@example.com",
            password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
            role="admin"
        )

        candidate_user = User(
            username="nguyenvana",
            email="vana@example.com",
            password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
            role="candidate"
        )

        company_user = User(
            username="techcorp",
            email="hr@techcorp.com",
            password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
            role="company"
        )

        db.session.add_all([admin, candidate_user, company_user])
        db.session.commit()

        # --- Tạo CandidateProfile ---
        candidate_profile = CandidateProfile(
            user_id=candidate_user.id,
            full_name="Nguyen Van A",
            phone="0123456789",
            skills="Python, Flask, SQLAlchemy",
            experience="2 years Backend Developer",
            education="Bachelor of Computer Science"
        )
        db.session.add(candidate_profile)
        db.session.commit()

        # --- Tạo Company ---
        company = Company(
            user_id=company_user.id,
            name="TechCorp",
            address="123 Hoang Quoc Viet, Hanoi"
        )
        db.session.add(company)
        db.session.commit()

        # --- Tạo Job ---
        job1 = Job(
            company_id=company.id,
            title="Backend Developer",
            description="Phát triển hệ thống API cho ứng dụng web.",
            location="Hanoi",
            salary="20-25 triệu",
            created_at=datetime.utcnow()
        )
        job2 = Job(
            company_id=company.id,
            title="Frontend Developer",
            description="Phát triển giao diện ReactJS.",
            location="Hanoi",
            salary="18-22 triệu",
            created_at=datetime.utcnow()
        )

        db.session.add_all([job1, job2])
        db.session.commit()

        # --- Tạo Application ---
        application = Application(
            candidate_profile_id=candidate_profile.id,
            job_id=job1.id,
            status=ApplicationStatus.PENDING,
            applied_at=datetime.utcnow()
        )
        db.session.add(application)
        db.session.commit()

        print("✅ Dữ liệu mẫu đã được tạo thành công!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Lỗi khi tạo dữ liệu mẫu: {e}")


if __name__ == "__main__":
    with app.app_context():
        seed_data()
