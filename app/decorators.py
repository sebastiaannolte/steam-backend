from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin is True:
            return f(*args, **kwargs)
        else:
            return abort(401)

    return wrap
