from datetime import datetime

from flask_apscheduler import APScheduler

from database.database import db
from backend.models.reminder import Reminder
from backend.models.notification import Notification
from backend.models.appointment import Appointment
from backend.models.follow_up import FollowUp
from backend.models.patient import Patient


scheduler = APScheduler()


def process_due_reminders():

    # APScheduler runs outside the normal Flask request context,
    # so we explicitly create an application context.
    app = scheduler.app

    with app.app_context():

        now = datetime.now()

        due_reminders = Reminder.query.filter(
            Reminder.scheduled_at <= now,
            Reminder.sent == False
        ).all()

        print(
            f"[REMINDER SCHEDULER] "
            f"Checking reminders at {now}"
        )

        print(
            f"[REMINDER SCHEDULER] "
            f"Due reminders found: {len(due_reminders)}"
        )

        for reminder in due_reminders:

            user_id = None
            message = ""

            # ------------------------------------------
            # Appointment reminder
            # ------------------------------------------

            if reminder.appointment_id:

                appointment = Appointment.query.get(
                    reminder.appointment_id
                )

                if appointment:

                    patient = Patient.query.get(
                        appointment.patient_id
                    )

                    if patient:

                        user_id = patient.user_id

                        message = (
                            "Reminder: You have an upcoming "
                            f"appointment on "
                            f"{appointment.appointment_date.isoformat()}."
                        )

            # ------------------------------------------
            # Follow-up reminder
            # ------------------------------------------

            elif reminder.follow_up_id:

                follow_up = FollowUp.query.get(
                    reminder.follow_up_id
                )

                if follow_up:

                    appointment = Appointment.query.get(
                        follow_up.appointment_id
                    )

                    if appointment:

                        patient = Patient.query.get(
                            appointment.patient_id
                        )

                        if patient:

                            user_id = patient.user_id

                            if follow_up.follow_up_date:

                                message = (
                                    "Reminder: You have a follow-up "
                                    "consultation scheduled for "
                                    f"{follow_up.follow_up_date.isoformat()}."
                                )

                            else:

                                message = (
                                    "Reminder: You have a pending "
                                    "follow-up consultation."
                                )

            # ------------------------------------------
            # Create notification
            # ------------------------------------------

            if user_id and message:

                notification = Notification(
                    user_id=user_id,
                    notification_type="reminder",
                    message=message,
                    sent=False
                )

                db.session.add(notification)

                reminder.sent = True

                print(
                    f"[REMINDER SCHEDULER] "
                    f"Processed reminder #{reminder.id}"
                )

        db.session.commit()


def start_scheduler(app):

    scheduler.init_app(app)

    scheduler.add_job(
        id="process_due_reminders",
        func=process_due_reminders,
        trigger="interval",
        minutes=1,
        replace_existing=True
    )

    scheduler.start()