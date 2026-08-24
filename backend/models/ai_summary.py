from datetime import datetime

from database.database import db


class AISummary(db.Model):
    __tablename__ = "ai_summaries"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id"),
        nullable=False,
        unique=True
    )

    urgency_level = db.Column(
        db.String(20),
        nullable=False
    )

    chief_complaint = db.Column(
        db.Text,
        nullable=False
    )

    suggested_question_1 = db.Column(
        db.Text,
        nullable=False
    )

    suggested_question_2 = db.Column(
        db.Text,
        nullable=False
    )

    suggested_question_3 = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )