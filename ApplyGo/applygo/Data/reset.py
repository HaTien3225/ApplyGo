from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Xóa tất cả bảng đã được đăng ký
db.metadata.clear()

# Sau đó, có thể tạo lại bảng
# db.create_all()
