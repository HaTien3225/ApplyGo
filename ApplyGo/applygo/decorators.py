from functools import wraps
from flask import abort

from flask import request, redirect, url_for
from flask_login import current_user, login_required


def loggedin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect(url_for('index', next=request.url))

        return f(*args, **kwargs)

    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required  # đảm bảo user đã login
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)  # trả 403 Forbidden nếu không đủ quyền
            return f(*args, **kwargs)
        return decorated_function
    return decorator