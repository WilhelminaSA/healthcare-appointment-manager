from database.database import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    date_of_birth = db.Column(
        db.Date,
        nullable=True
    )

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    address = db.Column(
        db.String(255),
        nullable=True
    )