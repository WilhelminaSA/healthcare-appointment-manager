from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.database import db
from backend.models.reminder import Reminder
from backend.models.appointment import Appointment
from backend.models.follow_up import FollowUp
from backend.models.patient import Patient
from backend.models.doctor import Doctor


reminder_bp = Blueprint(
    "reminder",
    __name__,
    url_prefix="/api/reminders"
)


# --------------------------------------------------
# POST /api/reminders/
# Create a reminder
# --------------------------------------------------

@reminder_bp.route("/", methods=["POST"])
@jwt_required()
def create_reminder():

    user_id = int(get_jwt_identity())

    data = request.get_json()

    appointment_id = data.get("appointment_id")
    follow_up_id = data.get("follow_up_id")
    reminder_type = data.get("reminder_type")
    scheduled_at = data.get("scheduled_at")

    if not reminder_type or not scheduled_at:
        return jsonify({
            "message": "reminder_type and scheduled_at are required"
        }), 400

    if not appointment_id and not follow_up_id:
        return jsonify({
            "message": "appointment_id or follow_up_id is required"
        }), 400

    # ----------------------------------------------
    # Verify appointment ownership
    # ----------------------------------------------

    if appointment_id:

        appointment = Appointment.query.get(
            appointment_id
        )

        if not appointment:
            return jsonify({
                "message": "Appointment not found"
            }), 404

        patient = Patient.query.filter_by(
            user_id=user_id
        ).first()

        doctor = Doctor.query.filter_by(
            user_id=user_id
        ).first()

        if (
            not patient
            or appointment.patient_id != patient.id
        ) and (
            not doctor
            or appointment.doctor_id != doctor.id
        ):
            return jsonify({
                "message": "You are not authorized for this appointment"
            }), 403

    # ----------------------------------------------
    # Verify follow-up ownership
    # ----------------------------------------------

    if follow_up_id:

        follow_up = FollowUp.query.get(
            follow_up_id
        )

        if not follow_up:
            return jsonify({
                "message": "Follow-up not found"
            }), 404

        appointment = Appointment.query.get(
            follow_up.appointment_id
        )

        if not appointment:
            return jsonify({
                "message": "Related appointment not found"
            }), 404

        patient = Patient.query.filter_by(
            user_id=user_id
        ).first()

        doctor = Doctor.query.filter_by(
            user_id=user_id
        ).first()

        if (
            not patient
            or appointment.patient_id != patient.id
        ) and (
            not doctor
            or appointment.doctor_id != doctor.id
        ):
            return jsonify({
                "message": "You are not authorized for this follow-up"
            }), 403

    # ----------------------------------------------
    # Parse scheduled time
    # ----------------------------------------------

    try:
        scheduled_datetime = datetime.fromisoformat(
            scheduled_at
        )
    except ValueError:
        return jsonify({
            "message": "Invalid scheduled_at format. "
                       "Use YYYY-MM-DDTHH:MM:SS"
        }), 400

    reminder = Reminder(
        appointment_id=appointment_id,
        follow_up_id=follow_up_id,
        reminder_type=reminder_type,
        scheduled_at=scheduled_datetime,
        sent=False
    )

    db.session.add(reminder)
    db.session.commit()

    return jsonify({
        "message": "Reminder created successfully",
        "reminder_id": reminder.id
    }), 201


# --------------------------------------------------
# GET /api/reminders/
# View user's reminders
# --------------------------------------------------

@reminder_bp.route("/", methods=["GET"])
@jwt_required()
def get_my_reminders():

    user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    reminders = []

    if patient:

        appointments = Appointment.query.filter_by(
            patient_id=patient.id
        ).all()

        appointment_ids = [
            appointment.id
            for appointment in appointments
        ]

        follow_ups = FollowUp.query.filter(
            FollowUp.appointment_id.in_(appointment_ids)
        ).all() if appointment_ids else []

        follow_up_ids = [
            follow_up.id
            for follow_up in follow_ups
        ]

        reminders = Reminder.query.filter(
            db.or_(
                Reminder.appointment_id.in_(appointment_ids)
                if appointment_ids else False,
                Reminder.follow_up_id.in_(follow_up_ids)
                if follow_up_ids else False
            )
        ).all()

    elif doctor:

        appointments = Appointment.query.filter_by(
            doctor_id=doctor.id
        ).all()

        appointment_ids = [
            appointment.id
            for appointment in appointments
        ]

        follow_ups = FollowUp.query.filter(
            FollowUp.appointment_id.in_(appointment_ids)
        ).all() if appointment_ids else []

        follow_up_ids = [
            follow_up.id
            for follow_up in follow_ups
        ]

        reminders = Reminder.query.filter(
            db.or_(
                Reminder.appointment_id.in_(appointment_ids)
                if appointment_ids else False,
                Reminder.follow_up_id.in_(follow_up_ids)
                if follow_up_ids else False
            )
        ).all()

    else:
        return jsonify({
            "message": "User profile not found"
        }), 404

    result = []

    for reminder in reminders:

        result.append({
            "id": reminder.id,
            "appointment_id": reminder.appointment_id,
            "follow_up_id": reminder.follow_up_id,
            "reminder_type": reminder.reminder_type,
            "scheduled_at": reminder.scheduled_at.isoformat(),
            "sent": reminder.sent
        })

    return jsonify(result), 200