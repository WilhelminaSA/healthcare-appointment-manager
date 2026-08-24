from database.database import db


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id"),
        nullable=True
    )

    follow_up_id = db.Column(
        db.Integer,
        db.ForeignKey("follow_ups.id"),
        nullable=True
    )

    reminder_type = db.Column(
        db.String(30),
        nullable=False
    )

    scheduled_at = db.Column(
        db.DateTime,
        nullable=False
    )

    sent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )