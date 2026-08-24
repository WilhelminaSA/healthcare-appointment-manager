from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.database import db
from backend.models.notification import Notification


notification_bp = Blueprint(
    "notification",
    __name__,
    url_prefix="/api/notifications"
)


# --------------------------------------------------
# GET /api/notifications/
# View logged-in user's notifications
# --------------------------------------------------

@notification_bp.route("/", methods=["GET"])
@jwt_required()
def get_my_notifications():

    user_id = int(get_jwt_identity())

    notifications = Notification.query.filter_by(
        user_id=user_id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    result = []

    for notification in notifications:

        result.append({
            "id": notification.id,
            "notification_type": notification.notification_type,
            "message": notification.message,
            "sent": notification.sent,
            "created_at": notification.created_at.isoformat()
        })

    return jsonify(result), 200