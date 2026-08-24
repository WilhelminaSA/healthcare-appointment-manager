from datetime import datetime

from database.database import db


class Medication(db.Model):
    __tablename__ = "medications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    prescription_id = db.Column(
        db.Integer,
        db.ForeignKey("prescriptions.id"),
        nullable=False
    )

    medicine_name = db.Column(
        db.String(100),
        nullable=False
    )

    dosage = db.Column(
        db.String(100),
        nullable=True
    )

    frequency = db.Column(
        db.String(100),
        nullable=False
    )

    duration = db.Column(
        db.String(100),
        nullable=True
    )

    start_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    end_date = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )