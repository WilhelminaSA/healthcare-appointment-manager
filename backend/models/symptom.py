from database.database import db


class Symptom(db.Model):
    __tablename__ = "symptoms"

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointments.id"),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.now()
    )