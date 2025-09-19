from applygo import db, app
from applygo.models import User, CandidateProfile, Company, Job, Application, ApplicationStatus, UserRole, CvTemplate, \
    CompanyStatus, Category
import hashlib
from datetime import datetime, timedelta
import random
import string


def seed_data():
    try:
        # --- Xóa dữ liệu cũ ---
        db.session.query(Application).delete()
        db.session.query(Job).delete()
        db.session.query(Company).delete()
        db.session.query(CandidateProfile).delete()
        db.session.query(User).delete()
        db.session.query(CvTemplate).delete()
        db.session.query(Category).delete()
        db.session.commit()

        # --- Admin ---
        admin = User(
            username="admin",
            email="admin@example.com",
            password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
            role=UserRole.ADMIN.value,
            image_url="admin.png"
        )
        db.session.add(admin)
        db.session.commit()

        # --- Categories ---
        categories = [
            Category(name="IT - Software", description="Lập trình, phát triển phần mềm"),
            Category(name="Marketing", description="Tiếp thị, quảng cáo"),
            Category(name="Finance", description="Ngân hàng, tài chính"),
            Category(name="Design", description="Thiết kế đồ họa, UI/UX"),
            Category(name="Education", description="Giảng dạy, đào tạo")
        ]
        db.session.add_all(categories)
        db.session.commit()
        print("✅ Categories created")

        # --- CV Templates ---
        templates = [
            CvTemplate(name="Simple", html_file="simple", preview_image="simple.png"),
            CvTemplate(name="Modern", html_file="modern", preview_image="modern.png"),
            CvTemplate(name="Professional", html_file="professional", preview_image="professional.png")
        ]
        db.session.add_all(templates)
        db.session.commit()
        print("✅ CV Templates created")

        # --- Ảnh mẫu ---
        user_images = [
            "avatar1.png",
            "avatar2.png",
            "avatar3.png",
            "avatar4.png",
        ]

        company_logos = [
            "logo1.png",
            "logo2.png",
            "logo3.png",
            "logo4.png",
        ]

        # --- 20 Candidates ---
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
        cv_template_files = [t.html_file for t in templates]
        candidates = []

        for i in range(1, 21):
            user = User(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
                role=UserRole.CANDIDATE.value,
                image_url=random.choice(user_images)  # avatar
            )
            db.session.add(user)
            db.session.commit()

            profile = CandidateProfile(
                user_id=user.id,
                full_name=f"Candidate {i}",
                phone=f"0900{str(i).zfill(4)}",
                skills=random.choice(skills_list),
                experience=f"{random.randint(1, 10)} years experience",
                education="Bachelor of Computer Science",
                cv_template=random.choice(cv_template_files)
            )
            db.session.add(profile)
            db.session.commit()
            candidates.append(profile)

        print("✅ Candidates created")

        # --- 10 Companies ---
        companies = []
        for i in range(1, 11):
            user = User(
                username=f"company{i}",
                email=f"company{i}@example.com",
                password=hashlib.md5("123456".encode("utf-8")).hexdigest(),
                role=UserRole.COMPANY.value,
                image_url=random.choice(company_logos)  # ảnh user của công ty
            )
            db.session.add(user)
            db.session.commit()

            company = Company(
                user_id=user.id,
                name=f"Company {i}",
                status=CompanyStatus.APPROVED.value,
                mst=''.join(random.choices(string.digits, k=10)),
                address=f"{i*10} Nguyen Trai, Hanoi",
                website=f"www.company{i}.com",
                logo_url=random.choice(company_logos)  # logo công ty
            )
            db.session.add(company)
            db.session.commit()
            companies.append(company)

        print("✅ Companies created")

        # --- 50 Jobs ---
        jobs = []
        for company in companies:
            for j in range(1, 6):
                created_offset = random.randint(0, 30)
                job = Job(
                    company_id=company.id,
                    category_id=random.choice(categories).id,
                    title=f"Job {j} at {company.name}",
                    description=f"Job description for Job {j} at {company.name}",
                    location=random.choice(["Hanoi", "Ho Chi Minh", "Da Nang"]),
                    salary=f"{15 + j * 5}-{20 + j * 5} triệu",
                    created_at=datetime.now() - timedelta(days=created_offset)
                )
                db.session.add(job)
                db.session.commit()
                jobs.append(job)

        print("✅ Jobs created")

        # --- Applications ---
        for candidate in candidates:
            applied_jobs = random.sample(jobs, k=5)
            for job in applied_jobs:
                application = Application(
                    candidate_profile_id=candidate.id,
                    job_id=job.id,
                    status=random.choice([status.value for status in ApplicationStatus]),
                    applied_at=datetime.now() - timedelta(days=random.randint(0, 30))
                )
                db.session.add(application)
        db.session.commit()

        print("✅ Applications created")
        print("🎉 Seed data generated successfully!")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error seeding data: {e}")


if __name__ == "__main__":
    with app.app_context():
        seed_data()
