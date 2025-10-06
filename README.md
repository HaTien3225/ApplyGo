# 💼 ApplyGo - Job Search Platform

This project provides a **Job Search and Recruitment Management System** with features such as job posting, candidate application, recruiter dashboard, and real-time notifications.  
The system is built with **Python Flask (backend)**, **MySQL (database)**, **Firebase (notifications)**, and deployed on **PythonAnywhere**.  
It supports multiple user roles: **Admin, Recruiter, and Job Seeker**.

---

## ✨ Features

- **User Authentication & Role-based Authorization** (Admin, Recruiter, Job Seeker)  
- **Job Management** (create, update, delete job postings)  
- **Job Search & Filtering** (by title, skills, location, salary range)  
- **Application Management** (apply for jobs, track application status)  
- **Recruiter Dashboard** (manage postings, view applicants)  
- **Notifications** (via Firebase Cloud Messaging or email)  
- **Admin Panel** (user management, statistics, and reports)  
- **Responsive Design** (optimized for both desktop and mobile)

---

## 🧰 Technologies Used

### 🖥️ Frontend
- HTML  
- CSS (TailwindCSS)  
- JavaScript  
- Jinja2 (Flask templating)

### ⚙️ Backend
- Python  
- Flask (RESTful API)  
- Flask-SQLAlchemy  
- Flask-JWT-Extended (for authentication)  
- Flask-Mail (for email notifications)

### 🗄️ Database
- MySQL 8.0+

### ☁️ Others
- Firebase Cloud Messaging  
- PythonAnywhere (deployment)  

---

## ⚙️ Configuration

### Backend (Flask)
- **IDE:** VS Code / PyCharm  
- **Python version:** 3.10+  
- **Virtual Environment:** venv  
- **Framework:** Flask  
- **ORM:** SQLAlchemy  
- **Authentication:** JWT  

**Create a database named:**
applygo_db

makefile


**Update your configuration file (`config.py`):**
```python
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:your_password@localhost/applygo_db"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "your_secret_key"

# Firebase config
FIREBASE_CREDENTIAL_PATH = "firebase-credentials.json"
Example usage in app.py:

python

from flask_sqlalchemy import SQLAlchemy
from config import *

app.config.from_object('config')
db = SQLAlchemy(app)
💻 Installation
1️⃣ Clone the repository
bash

git clone https://github.com/your-username/applygo-job-platform.git
cd applygo-job-platform
2️⃣ Create and activate virtual environment
bash

python -m venv venv
venv\Scripts\activate       # (Windows)
source venv/bin/activate    # (macOS/Linux)
3️⃣ Install dependencies
bash

pip install -r requirements.txt
4️⃣ Set up database
bash

flask db init
flask db migrate
flask db upgrade
5️⃣ Run the project
bash

flask run
App will be running at:
👉 http://127.0.0.1:5000/

🌐 Deployment (PythonAnywhere)
Create a new web app on PythonAnywhere.

Choose Flask as the framework.

Upload your project folder using the Files tab.

Update your WSGI configuration file to point to app.py.

Add your environment variables (database credentials, secret key).

Reload your app to deploy changes.

🧩 Database Schema (MySQL)
Table	Description
users	Stores user details (email, password, role)
jobs	Job postings created by recruiters
applications	Job applications submitted by seekers
notifications	Stores user notifications and timestamps

Relationships:

One Recruiter → Many Jobs

One Job → Many Applications

One Job Seeker → Many Applications

🔥 Firebase Integration
Used for:

Real-time job posting updates

Push notifications to users

python

import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("firebase-credentials.json")
firebase_admin.initialize_app(cred)
🧠 Folder Structure
php

ApplyGo/
│
├── app.py                  # Main Flask app entry point
├── config.py               # Configuration (DB, Firebase, Secret Key)
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── job.py
│   ├── application.py
│
├── routes/                 # Flask Blueprints (API routes)
│   ├── auth.py
│   ├── job_routes.py
│   ├── application_routes.py
│
├── templates/              # HTML templates
│   ├── index.html
│   ├── login.html
│   ├── dashboard.html
│
├── static/                 # CSS, JS, images
├── firebase_service.py     # Firebase integration
├── requirements.txt
└── README.md
🧑‍💻 Developer
Nguyễn Văn A
🎓 Student at Ho Chi Minh City Open University
💻 Python & Flask Developer

📫 Contact:

GitHub: https://github.com/nguyenvana

LinkedIn: https://www.linkedin.com/in/nguyenvana

Email: nguyenvana@example.com

🌟 Future Enhancements
AI-powered job matching and recommendation engine

Resume parsing from PDF

Integrated chat between recruiters and candidates

Google Maps API integration for job location visualization

🪪 License
This project is licensed under the MIT License – see the LICENSE file for details.
