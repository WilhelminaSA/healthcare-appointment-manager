from datetime import datetime

from database.database import db


class SlotHold(db.Model):

    __tablename__ = "slot_holds"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    appointment_date = db.Column(
        db.DateTime,
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )