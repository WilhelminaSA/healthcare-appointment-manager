from sqlalchemy import text

from backend.app import app
from database.database import db


with app.app_context():

    db.session.execute(
        text(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            uq_slot_hold_doctor_appointment
            ON slot_holds (doctor_id, appointment_date)
            """
        )
    )

    db.session.commit()

    print("Slot hold index created successfully")
