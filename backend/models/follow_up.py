from datetime import datetime

from database.database import db


class FollowUp(db.Model):
    __tablename__ = "follow_ups"

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id"),
        nullable=False
    )

    follow_up_date = db.Column(
        db.DateTime,
        nullable=True
    )

    notes = db.Column(
        db.Text,
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )