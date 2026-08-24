
from datetime import datetime

from sqlalchemy import Index

from database.database import db


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    appointment_date = db.Column(
        db.DateTime,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="scheduled"
    )

    reason = db.Column(
        db.String(500),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    __table_args__ = (
        Index(
            "uq_scheduled_doctor_appointment",
            "doctor_id",
            "appointment_date",
            unique=True,
            postgresql_where=(
                db.text("status = 'scheduled'")
            )
        ),
    )
