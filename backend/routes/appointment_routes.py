from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from database.database import db
from backend.models.appointment import Appointment
from backend.models.patient import Patient
from backend.models.doctor import Doctor
from backend.models.notification import Notification
from backend.models.working_hour import WorkingHour
from backend.models.doctor_leave import DoctorLeave
from backend.models.slot_hold import SlotHold


appointment_bp = Blueprint(
    "appointment",
    __name__,
    url_prefix="/api/appointments"
)


# ==================================================
# POST /api/appointments/hold
# Patient temporarily holds an appointment slot
# ==================================================

@appointment_bp.route("/hold", methods=["POST"])
@jwt_required()
def hold_appointment_slot():

    user_id = int(get_jwt_identity())

    # --------------------------------------------------
    # Verify patient
    # --------------------------------------------------

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if not patient:
        return jsonify({
            "message": "Only patients can hold appointment slots"
        }), 403

    # --------------------------------------------------
    # Get request data
    # --------------------------------------------------

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    doctor_id = data.get("doctor_id")
    appointment_date = data.get("appointment_date")

    if not doctor_id or not appointment_date:
        return jsonify({
            "message": (
                "doctor_id and appointment_date are required"
            )
        }), 400

    # --------------------------------------------------
    # Verify doctor
    # --------------------------------------------------

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({
            "message": "Doctor not found"
        }), 404

    # --------------------------------------------------
    # Parse appointment datetime
    # --------------------------------------------------

    try:
        appointment_datetime = datetime.fromisoformat(
            appointment_date
        )

    except (ValueError, TypeError):
        return jsonify({
            "message": (
                "Invalid appointment_date format. "
                "Use YYYY-MM-DDTHH:MM:SS"
            )
        }), 400

    # --------------------------------------------------
    # Appointment must be in the future
    # --------------------------------------------------

    now = datetime.now()

    if appointment_datetime < now:
        return jsonify({
            "message": "Appointment date must be in the future"
        }), 400

    appointment_date_only = appointment_datetime.date()

    # --------------------------------------------------
    # Check doctor leave
    # --------------------------------------------------

    doctor_leave = DoctorLeave.query.filter_by(
        doctor_id=doctor.id,
        leave_date=appointment_date_only
    ).first()

    if doctor_leave:
        return jsonify({
            "message": "Doctor is on leave on this date"
        }), 409

    # --------------------------------------------------
    # Determine day of week
    # --------------------------------------------------

    day_of_week = appointment_date_only.weekday()

    # --------------------------------------------------
    # Find working hours
    # --------------------------------------------------

    working_hour = WorkingHour.query.filter_by(
        doctor_id=doctor.id,
        day_of_week=day_of_week
    ).first()

    if not working_hour:
        return jsonify({
            "message": "Doctor is not working on this day"
        }), 409

    # --------------------------------------------------
    # Construct working-hour boundaries
    # --------------------------------------------------

    working_start = datetime.combine(
        appointment_date_only,
        working_hour.start_time
    )

    working_end = datetime.combine(
        appointment_date_only,
        working_hour.end_time
    )

    # --------------------------------------------------
    # Check appointment is inside working hours
    # --------------------------------------------------

    if (
        appointment_datetime < working_start
        or appointment_datetime >= working_end
    ):
        return jsonify({
            "message": (
                "Selected appointment time is outside "
                "the doctor's working hours"
            )
        }), 409

    # --------------------------------------------------
    # Check exact slot alignment
    # --------------------------------------------------

    slot_duration = working_hour.slot_duration

    if slot_duration <= 0:
        return jsonify({
            "message": "Invalid slot duration configured for doctor"
        }), 500

    elapsed_seconds = (
        appointment_datetime - working_start
    ).total_seconds()

    slot_duration_seconds = slot_duration * 60

    if (
        elapsed_seconds < 0
        or elapsed_seconds % slot_duration_seconds != 0
    ):
        return jsonify({
            "message": (
                "Selected appointment time is not "
                "a valid available slot"
            )
        }), 409

    # --------------------------------------------------
    # Calculate slot end
    # --------------------------------------------------

    slot_end = appointment_datetime + timedelta(
        minutes=slot_duration
    )

    # --------------------------------------------------
    # Make sure complete slot fits inside working hours
    # --------------------------------------------------

    if slot_end > working_end:
        return jsonify({
            "message": (
                "Selected appointment slot extends "
                "beyond the doctor's working hours"
            )
        }), 409

    # --------------------------------------------------
    # Check existing scheduled appointment
    # --------------------------------------------------

    existing_appointment = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=appointment_datetime
    ).filter(
        Appointment.status == "scheduled"
    ).first()

    if existing_appointment:
        return jsonify({
            "message": "Doctor is already booked for this slot"
        }), 409

    # --------------------------------------------------
    # Remove expired holds
    # --------------------------------------------------

    expired_holds = SlotHold.query.filter(
        SlotHold.expires_at <= now
    ).all()

    for expired_hold in expired_holds:
        db.session.delete(expired_hold)

    db.session.flush()

    # --------------------------------------------------
    # Check whether this patient already holds the slot
    # --------------------------------------------------

    existing_patient_hold = SlotHold.query.filter_by(
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_date=appointment_datetime
    ).first()

    if existing_patient_hold:

        return jsonify({
            "message": "You already hold this slot",
            "hold_id": existing_patient_hold.id,
            "doctor_id": doctor.id,
            "appointment_date": (
                appointment_datetime.isoformat()
            ),
            "expires_at": (
                existing_patient_hold.expires_at.isoformat()
            ),
            "status": "held"
        }), 200

    # --------------------------------------------------
    # Check whether another patient holds the slot
    # --------------------------------------------------

    existing_hold = SlotHold.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=appointment_datetime
    ).first()

    if existing_hold:

        return jsonify({
            "message": (
                "This slot is currently held "
                "by another patient"
            )
        }), 409

    # --------------------------------------------------
    # Create 5-minute hold
    # --------------------------------------------------

    expires_at = now + timedelta(minutes=5)

    hold = SlotHold(
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_date=appointment_datetime,
        expires_at=expires_at
    )

    db.session.add(hold)

    # --------------------------------------------------
    # Database-level concurrency protection
    #
    # A unique index on:
    #
    # doctor_id + appointment_date
    #
    # prevents two patients from holding
    # the same slot simultaneously.
    # --------------------------------------------------

    try:

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return jsonify({
            "message": (
                "This slot was just held "
                "by another patient"
            )
        }), 409

    # --------------------------------------------------
    # Return response
    # --------------------------------------------------

    return jsonify({
        "message": "Appointment slot held successfully",
        "hold_id": hold.id,
        "doctor_id": doctor.id,
        "appointment_date": (
            appointment_datetime.isoformat()
        ),
        "expires_at": expires_at.isoformat(),
        "status": "held"
    }), 201


# ==================================================
# POST /api/appointments/
# Patient confirms a held appointment
# ==================================================

@appointment_bp.route("/", methods=["POST"])
@jwt_required()
def create_appointment():

    user_id = int(get_jwt_identity())

    # --------------------------------------------------
    # Verify patient
    # --------------------------------------------------

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if not patient:
        return jsonify({
            "message": "Only patients can book appointments"
        }), 403

    # --------------------------------------------------
    # Get request data
    # --------------------------------------------------

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    doctor_id = data.get("doctor_id")
    appointment_date = data.get("appointment_date")
    reason = data.get("reason")
    hold_id = data.get("hold_id")

    if not doctor_id or not appointment_date:
        return jsonify({
            "message": (
                "doctor_id and appointment_date are required"
            )
        }), 400

    if not hold_id:
        return jsonify({
            "message": (
                "hold_id is required. "
                "Please hold the slot before booking."
            )
        }), 400

    # --------------------------------------------------
    # Verify doctor
    # --------------------------------------------------

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({
            "message": "Doctor not found"
        }), 404

    # --------------------------------------------------
    # Parse appointment datetime
    # --------------------------------------------------

    try:
        appointment_datetime = datetime.fromisoformat(
            appointment_date
        )

    except (ValueError, TypeError):
        return jsonify({
            "message": (
                "Invalid appointment_date format. "
                "Use YYYY-MM-DDTHH:MM:SS"
            )
        }), 400

    # --------------------------------------------------
    # Appointment must be in the future
    # --------------------------------------------------

    now = datetime.now()

    if appointment_datetime < now:
        return jsonify({
            "message": "Appointment date must be in the future"
        }), 400

    appointment_date_only = appointment_datetime.date()

    # --------------------------------------------------
    # Verify hold belongs to this patient and doctor
    # --------------------------------------------------

    hold = SlotHold.query.filter_by(
        id=hold_id,
        doctor_id=doctor.id,
        patient_id=patient.id,
        appointment_date=appointment_datetime
    ).first()

    if not hold:
        return jsonify({
            "message": (
                "Valid slot hold not found. "
                "Please hold the slot again."
            )
        }), 409

    # --------------------------------------------------
    # Check hold expiration
    # --------------------------------------------------

    if hold.expires_at <= now:

        db.session.delete(hold)
        db.session.commit()

        return jsonify({
            "message": (
                "Your slot hold has expired. "
                "Please select the slot again."
            )
        }), 409

    # --------------------------------------------------
    # Check doctor leave
    # --------------------------------------------------

    doctor_leave = DoctorLeave.query.filter_by(
        doctor_id=doctor.id,
        leave_date=appointment_date_only
    ).first()

    if doctor_leave:
        return jsonify({
            "message": "Doctor is on leave on this date"
        }), 409

    # --------------------------------------------------
    # Determine day of week
    # --------------------------------------------------

    day_of_week = appointment_date_only.weekday()

    # --------------------------------------------------
    # Find working hours
    # --------------------------------------------------

    working_hour = WorkingHour.query.filter_by(
        doctor_id=doctor.id,
        day_of_week=day_of_week
    ).first()

    if not working_hour:
        return jsonify({
            "message": "Doctor is not working on this day"
        }), 409

    # --------------------------------------------------
    # Construct working-hour boundaries
    # --------------------------------------------------

    working_start = datetime.combine(
        appointment_date_only,
        working_hour.start_time
    )

    working_end = datetime.combine(
        appointment_date_only,
        working_hour.end_time
    )

    # --------------------------------------------------
    # Check appointment is inside working hours
    # --------------------------------------------------

    if (
        appointment_datetime < working_start
        or appointment_datetime >= working_end
    ):
        return jsonify({
            "message": (
                "Selected appointment time is outside "
                "the doctor's working hours"
            )
        }), 409

    # --------------------------------------------------
    # Check exact slot alignment
    # --------------------------------------------------

    slot_duration = working_hour.slot_duration

    if slot_duration <= 0:
        return jsonify({
            "message": "Invalid slot duration configured for doctor"
        }), 500

    elapsed_seconds = (
        appointment_datetime - working_start
    ).total_seconds()

    slot_duration_seconds = slot_duration * 60

    if (
        elapsed_seconds < 0
        or elapsed_seconds % slot_duration_seconds != 0
    ):
        return jsonify({
            "message": (
                "Selected appointment time is not "
                "a valid available slot"
            )
        }), 409

    # --------------------------------------------------
    # Calculate slot end
    # --------------------------------------------------

    slot_end = appointment_datetime + timedelta(
        minutes=slot_duration
    )

    # --------------------------------------------------
    # Make sure complete slot fits inside working hours
    # --------------------------------------------------

    if slot_end > working_end:
        return jsonify({
            "message": (
                "Selected appointment slot extends "
                "beyond the doctor's working hours"
            )
        }), 409

    # --------------------------------------------------
    # Prevent double booking
    # --------------------------------------------------

    existing_appointment = Appointment.query.filter_by(
        doctor_id=doctor.id,
        appointment_date=appointment_datetime
    ).filter(
        Appointment.status == "scheduled"
    ).first()

    if existing_appointment:
        return jsonify({
            "message": "Doctor is already booked for this slot"
        }), 409

    # --------------------------------------------------
    # Create appointment
    # --------------------------------------------------

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=appointment_datetime,
        reason=reason,
        status="scheduled"
    )

    db.session.add(appointment)

    # --------------------------------------------------
    # Database-level double-booking protection
    # --------------------------------------------------

    try:

        db.session.flush()

    except IntegrityError:

        db.session.rollback()

        return jsonify({
            "message": "Doctor is already booked for this slot"
        }), 409

    # --------------------------------------------------
    # Create notification
    # --------------------------------------------------

    notification = Notification(
        user_id=user_id,
        notification_type="appointment_booked",
        message=(
            f"Your appointment with doctor #{doctor.id} "
            f"has been booked successfully for "
            f"{appointment_datetime.isoformat()}."
        ),
        sent=False
    )

    db.session.add(notification)

    # --------------------------------------------------
    # Remove the consumed hold
    # --------------------------------------------------

    db.session.delete(hold)

    # --------------------------------------------------
    # Commit transaction
    # --------------------------------------------------

    try:

        db.session.commit()

    except IntegrityError:

        db.session.rollback()

        return jsonify({
            "message": "Doctor is already booked for this slot"
        }), 409

    # --------------------------------------------------
    # Return response
    # --------------------------------------------------

    return jsonify({
        "message": "Appointment booked successfully",
        "appointment_id": appointment.id,
        "doctor_id": doctor.id,
        "appointment_date": (
            appointment_datetime.isoformat()
        ),
        "slot": {
            "start_time": appointment_datetime.strftime("%H:%M"),
            "end_time": slot_end.strftime("%H:%M")
        },
        "status": appointment.status
    }), 201


# ==================================================
# GET /api/appointments/
# Patient views all their appointments
# ==================================================

@appointment_bp.route("/", methods=["GET"])
@jwt_required()
def get_my_appointments():

    user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if not patient:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    appointments = Appointment.query.filter_by(
        patient_id=patient.id
    ).order_by(
        Appointment.appointment_date.asc()
    ).all()

    result = []

    for appointment in appointments:

        doctor = Doctor.query.get(
            appointment.doctor_id
        )

        result.append({
            "id": appointment.id,
            "doctor_id": appointment.doctor_id,
            "doctor_specialization": (
                doctor.specialization
                if doctor else None
            ),
            "appointment_date": (
                appointment.appointment_date.isoformat()
            ),
            "status": appointment.status,
            "reason": appointment.reason
        })

    return jsonify(result), 200


# ==================================================
# GET /api/appointments/<appointment_id>
# Patient views one specific appointment
# ==================================================

@appointment_bp.route("/<int:appointment_id>", methods=["GET"])
@jwt_required()
def get_single_appointment(appointment_id):

    user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if not patient:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()

    if not appointment:
        return jsonify({
            "message": "Appointment not found"
        }), 404

    doctor = Doctor.query.get(
        appointment.doctor_id
    )

    return jsonify({
        "id": appointment.id,
        "patient_id": appointment.patient_id,
        "doctor_id": appointment.doctor_id,
        "doctor_specialization": (
            doctor.specialization
            if doctor else None
        ),
        "appointment_date": (
            appointment.appointment_date.isoformat()
        ),
        "status": appointment.status,
        "reason": appointment.reason
    }), 200


# ==================================================
# DELETE /api/appointments/<appointment_id>
# Patient cancels an appointment
# ==================================================

@appointment_bp.route("/<int:appointment_id>", methods=["DELETE"])
@jwt_required()
def cancel_appointment(appointment_id):

    user_id = int(get_jwt_identity())

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if not patient:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()

    if not appointment:
        return jsonify({
            "message": "Appointment not found"
        }), 404

    if appointment.status == "cancelled":
        return jsonify({
            "message": "Appointment is already cancelled"
        }), 400

    if appointment.status == "completed":
        return jsonify({
            "message": "Completed appointments cannot be cancelled"
        }), 400

    appointment.status = "cancelled"

    notification = Notification(
        user_id=user_id,
        notification_type="appointment_cancelled",
        message=(
            f"Your appointment #{appointment.id} "
            f"has been cancelled successfully."
        ),
        sent=False
    )

    db.session.add(notification)
    db.session.commit()

    return jsonify({
        "message": "Appointment cancelled successfully",
        "appointment_id": appointment.id
    }), 200


# ==================================================
# GET /api/appointments/doctors
# Patient views available doctors
# ==================================================

@appointment_bp.route("/doctors", methods=["GET"])
@jwt_required()
def get_doctors():

    doctors = Doctor.query.all()

    result = []

    for doctor in doctors:

        result.append({
            "doctor_id": doctor.id,
            "specialization": doctor.specialization,
            "phone": doctor.phone
        })

    return jsonify(result), 200


# ==================================================
# GET /api/appointments/doctor
# Doctor views their appointments
# ==================================================

@appointment_bp.route("/doctor", methods=["GET"])
@jwt_required()
def get_doctor_appointments():

    user_id = int(get_jwt_identity())

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    if not doctor:
        return jsonify({
            "message": "Doctor profile not found"
        }), 404

    appointments = Appointment.query.filter_by(
        doctor_id=doctor.id
    ).order_by(
        Appointment.appointment_date.asc()
    ).all()

    result = []

    for appointment in appointments:

        patient = Patient.query.get(
            appointment.patient_id
        )

        result.append({
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "appointment_date": (
                appointment.appointment_date.isoformat()
            ),
            "status": appointment.status,
            "reason": appointment.reason,
            "patient_phone": (
                patient.phone if patient else None
            ),
            "patient_address": (
                patient.address if patient else None
            )
        })

    return jsonify(result), 200
