from applygo import db, app
from applygo.models import User, CandidateProfile, Company, Job, Application, ApplicationStatus, UserRole
import hashlib
from datetime import datetime, timedelta
import random

def seed_large():
    try:
        # Xóa dữ liệu cũ
        db.session.query(Application).delete()
        db.session.query(Job).delete()
        db.session.query(Company).delete()
        db.session.query(CandidateProfile).delete()
        db.session.query(User).delete()

        # --- Tạo Admin ---
        admin = User(
            username="admin",
            email="admin@example.com",
            password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
            role=UserRole.ADMIN
        )
        db.session.add(admin)
        db.session.commit()

        # --- Tạo 20 ứng viên ---
        candidates = []
        skills_list = [
            "Python, Flask, SQLAlchemy",
            "Java, Spring Boot",
            "JavaScript, ReactJS",
            "C#, .NET",
            "Ruby on Rails",
            "Go, Docker, Kubernetes",
            "PHP, Laravel",
            "Node.js, Express",
            "Machine Learning, Python",
            "Data Analysis, Python, SQL"
        ]
        for i in range(1, 21):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
                role=UserRole.CANDIDATE
            )
            db.session.add(user)
            db.session.commit()

            profile = CandidateProfile(
                user_id=user.id,
                full_name=f"Candidate {i}",
                phone=f"0900{str(i).zfill(4)}",
                skills=random.choice(skills_list),
                experience=f"{random.randint(1,10)} years experience",
                education="Bachelor of Computer Science"
            )
            db.session.add(profile)
            db.session.commit()
            candidates.append(profile)

        # --- Tạo 10 công ty ---
        companies = []
        for i in range(1, 11):
            user = User(
                username=f"company{i}",
                email=f"company{i}@example.com",
                password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
                role=UserRole.COMPANY
            )
            db.session.add(user)
            db.session.commit()

            company = Company(
                user_id=user.id,
                name=f"Company {i}",
                address=f"{i*10} Nguyen Trai, Hanoi",
                website=f"www.company{i}.com"
            )
            db.session.add(company)
            db.session.commit()
            companies.append(company)

        # --- Tạo 50 job (mỗi công ty 5 job) ---
        jobs = []
        for company in companies:
            for j in range(1, 6):
                created_offset = random.randint(0, 30)
                job = Job(
                    company_id=company.id,
                    title=f"Job {j} at {company.name}",
                    description=f"Job description for Job {j} at {company.name}",
                    location=random.choice(["Hanoi", "Ho Chi Minh", "Da Nang"]),
                    salary=f"{15+j*5}-{20+j*5} triệu",
                    created_at=datetime.now() - timedelta(days=created_offset)
                )
                db.session.add(job)
                db.session.commit()
                jobs.append(job)

        # --- Tạo hồ sơ ứng tuyển ngẫu nhiên ---
        for candidate in candidates:
            applied_jobs = random.sample(jobs, k=5)
            for job in applied_jobs:
                application = Application(
                    candidate_profile_id=candidate.id,
                    job_id=job.id,
                    status=random.choice(list(ApplicationStatus)),
                    applied_at=datetime.now() - timedelta(days=random.randint(0, 30))
                )
                db.session.add(application)
        db.session.commit()

        print("✅ Dữ liệu siêu lớn đã được tạo thành công!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Lỗi khi tạo dữ liệu siêu lớn: {e}")

if __name__ == "__main__":
    with app.app_context():
        seed_large()
