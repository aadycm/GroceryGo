from database.db import db
from models import Notification


def notify_user(user_id, title, message):
    n = Notification(user_id=user_id, title=title, message=message)
    db.session.add(n)
    db.session.commit()
    return n


def broadcast_notification(title, message):
    n = Notification(user_id=None, title=title, message=message)
    db.session.add(n)
    db.session.commit()
    return n
