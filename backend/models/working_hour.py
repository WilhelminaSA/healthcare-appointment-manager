from database.database import db


class WorkingHour(db.Model):
    __tablename__ = "working_hours"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    day_of_week = db.Column(
        db.Integer,
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    slot_duration = db.Column(
        db.Integer,
        nullable=False
    )