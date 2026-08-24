from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.database import db
from backend.models.doctor import Doctor
from backend.models.working_hour import WorkingHour
from backend.models.doctor_leave import DoctorLeave
from backend.models.appointment import Appointment
from backend.models.patient import Patient
from backend.models.user import User
from backend.models.notification import Notification
from backend.models.slot_hold import SlotHold


availability_bp = Blueprint(
    "availability",
    __name__,
    url_prefix="/api/availability"
)


# ==================================================
# POST /api/availability/working-hours/<doctor_id>
# Admin configures a doctor's working hours
# ==================================================

@availability_bp.route(
    "/working-hours/<int:doctor_id>",
    methods=["POST"]
)
@jwt_required()
def create_working_hours(doctor_id):

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user or user.role != "admin":
        return jsonify({
            "message": "Only admins can configure working hours"
        }), 403

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({
            "message": "Doctor not found"
        }), 404

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    day_of_week = data.get("day_of_week")
    start_time = data.get("start_time")
    end_time = data.get("end_time")
    slot_duration = data.get("slot_duration")

    if (
        day_of_week is None
        or not start_time
        or not end_time
        or slot_duration is None
    ):
        return jsonify({
            "message": (
                "day_of_week, start_time, end_time and "
                "slot_duration are required"
            )
        }), 400

    try:
        day_of_week = int(day_of_week)
    except (ValueError, TypeError):
        return jsonify({
            "message": "day_of_week must be an integer from 0 to 6"
        }), 400

    if day_of_week < 0 or day_of_week > 6:
        return jsonify({
            "message": "day_of_week must be between 0 and 6"
        }), 400

    try:
        slot_duration = int(slot_duration)
    except (ValueError, TypeError):
        return jsonify({
            "message": "slot_duration must be an integer"
        }), 400

    if slot_duration <= 0:
        return jsonify({
            "message": "slot_duration must be greater than 0"
        }), 400

    try:
        parsed_start_time = datetime.strptime(
            start_time,
            "%H:%M"
        ).time()

        parsed_end_time = datetime.strptime(
            end_time,
            "%H:%M"
        ).time()

    except (ValueError, TypeError):
        return jsonify({
            "message": (
                "start_time and end_time must use HH:MM format"
            )
        }), 400

    if parsed_end_time <= parsed_start_time:
        return jsonify({
            "message": "end_time must be after start_time"
        }), 400

    existing = WorkingHour.query.filter_by(
        doctor_id=doctor.id,
        day_of_week=day_of_week
    ).first()

    if existing:
        return jsonify({
            "message": (
                "Working hours already exist for this "
                "doctor and day"
            )
        }), 409

    working_hour = WorkingHour(
        doctor_id=doctor.id,
        day_of_week=day_of_week,
        start_time=parsed_start_time,
        end_time=parsed_end_time,
        slot_duration=slot_duration
    )

    db.session.add(working_hour)
    db.session.commit()

    return jsonify({
        "message": "Working hours created successfully",
        "working_hour": {
            "id": working_hour.id,
            "doctor_id": working_hour.doctor_id,
            "day_of_week": working_hour.day_of_week,
            "start_time": working_hour.start_time.strftime("%H:%M"),
            "end_time": working_hour.end_time.strftime("%H:%M"),
            "slot_duration": working_hour.slot_duration
        }
    }), 201


# ==================================================
# GET /api/availability/working-hours/<doctor_id>
# View a doctor's working hours
# ==================================================

@availability_bp.route(
    "/working-hours/<int:doctor_id>",
    methods=["GET"]
)
@jwt_required()
def get_working_hours(doctor_id):

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({
            "message": "Doctor not found"
        }), 404

    working_hours = WorkingHour.query.filter_by(
        doctor_id=doctor.id
    ).order_by(
        WorkingHour.day_of_week.asc(),
        WorkingHour.start_time.asc()
    ).all()

    result = []

    for working_hour in working_hours:

        result.append({
            "id": working_hour.id,
            "doctor_id": working_hour.doctor_id,
            "day_of_week": working_hour.day_of_week,
            "start_time": (
                working_hour.start_time.strftime("%H:%M")
            ),
            "end_time": (
                working_hour.end_time.strftime("%H:%M")
            ),
            "slot_duration": working_hour.slot_duration
        })

    return jsonify(result), 200


# ==================================================
# POST /api/availability/leave/<doctor_id>
# Admin adds a doctor's leave
#
# If scheduled appointments already exist on the
# leave date:
#   1. Those appointments are cancelled.
#   2. A notification is created for each patient.
# ==================================================

@availability_bp.route(
    "/leave/<int:doctor_id>",
    methods=["POST"]
)
@jwt_required()
def create_doctor_leave(doctor_id):

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    # --------------------------------------------------
    # Verify admin
    # --------------------------------------------------

    if not user or user.role != "admin":
        return jsonify({
            "message": "Only admins can manage doctor leave"
        }), 403

    # --------------------------------------------------
    # Verify doctor
    # --------------------------------------------------

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({
            "message": "Doctor not found"
        }), 404

    # --------------------------------------------------
    # Get request data
    # --------------------------------------------------

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    leave_date = data.get("leave_date")
    reason = data.get("reason")

    if not leave_date:
        return jsonify({
            "message": "leave_date is required"
        }), 400

    # --------------------------------------------------
    # Parse leave date
    # Expected: YYYY-MM-DD
    # --------------------------------------------------

    try:

        parsed_leave_date = datetime.strptime(
            leave_date,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):

        return jsonify({
            "message": "leave_date must use YYYY-MM-DD format"
        }), 400

    # --------------------------------------------------
    # Prevent duplicate leave
    # --------------------------------------------------

    existing_leave = DoctorLeave.query.filter_by(
        doctor_id=doctor.id,
        leave_date=parsed_leave_date
    ).first()

    if existing_leave:

        return jsonify({
            "message": "Doctor already has leave on this date"
        }), 409

    # --------------------------------------------------
    # Find existing scheduled appointments
    # on the leave date
    # --------------------------------------------------

    affected_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == "scheduled",
        db.func.date(
            Appointment.appointment_date
        ) == parsed_leave_date
    ).all()

    # --------------------------------------------------
    # Create doctor leave
    # --------------------------------------------------

    doctor_leave = DoctorLeave(
        doctor_id=doctor.id,
        leave_date=parsed_leave_date,
        reason=reason
    )

    db.session.add(doctor_leave)

    # --------------------------------------------------
    # Cancel affected appointments and create
    # notifications for the patients
    # --------------------------------------------------

    affected_count = 0
    notification_count = 0

    for appointment in affected_appointments:

        # Cancel the appointment
        appointment.status = "cancelled"

        affected_count += 1

        # Find the patient
        patient = Patient.query.get(
            appointment.patient_id
        )

        if patient:

            # Create notification for the patient
            notification = Notification(
                user_id=patient.user_id,
                notification_type="doctor_leave",
                message=(
                    f"Your appointment #{appointment.id} "
                    f"with doctor #{doctor.id} on "
                    f"{parsed_leave_date.isoformat()} "
                    f"has been cancelled because the doctor "
                    f"is on leave."
                ),
                sent=False
            )

            db.session.add(notification)

            notification_count += 1

    # --------------------------------------------------
    # Commit everything together
    # --------------------------------------------------

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return jsonify({
            "message": "Failed to create doctor leave"
        }), 500

    # --------------------------------------------------
    # Return response
    # --------------------------------------------------

    return jsonify({
        "message": "Doctor leave added successfully",
        "leave": {
            "id": doctor_leave.id,
            "doctor_id": doctor_leave.doctor_id,
            "leave_date": doctor_leave.leave_date.isoformat(),
            "reason": doctor_leave.reason
        },
        "affected_appointments": affected_count,
        "notifications_created": notification_count
    }), 201


# ==================================================
# GET /api/availability/leave/<doctor_id>
# View a doctor's leave days
# ==================================================

@availability_bp.route(
    "/leave/<int:doctor_id>",
    methods=["GET"]
)
@jwt_required()
def get_doctor_leave(doctor_id):

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({
            "message": "Doctor not found"
        }), 404

    leaves = DoctorLeave.query.filter_by(
        doctor_id=doctor.id
    ).order_by(
        DoctorLeave.leave_date.asc()
    ).all()

    result = []

    for leave in leaves:

        result.append({
            "id": leave.id,
            "doctor_id": leave.doctor_id,
            "leave_date": leave.leave_date.isoformat(),
            "reason": leave.reason
        })

    return jsonify(result), 200


# ==================================================
# DELETE /api/availability/leave/<leave_id>
# Admin removes a doctor's leave
# ==================================================

@availability_bp.route(
    "/leave/<int:leave_id>",
    methods=["DELETE"]
)
@jwt_required()
def delete_doctor_leave(leave_id):

    user_id = int(get_jwt_identity())

    user = User.query.get(user_id)

    if not user or user.role != "admin":
        return jsonify({
            "message": "Only admins can manage doctor leave"
        }), 403

    doctor_leave = DoctorLeave.query.get(leave_id)

    if not doctor_leave:
        return jsonify({
            "message": "Leave record not found"
        }), 404

    db.session.delete(doctor_leave)
    db.session.commit()

    return jsonify({
        "message": "Doctor leave deleted successfully",
        "leave_id": leave_id
    }), 200


# ==================================================
# GET /api/availability/slots/<doctor_id>?date=YYYY-MM-DD
#
# Patient views available appointment slots
# ==================================================

# ==================================================
# GET /api/availability/slots/<doctor_id>?date=YYYY-MM-DD
#
# Patient views available appointment slots
#
# A slot is unavailable if:
#   1. Doctor is on leave
#   2. Doctor is not working
#   3. Slot is already booked
#   4. Slot is currently held by another patient
#
# Expired holds are removed automatically.
# ==================================================

@availability_bp.route(
    "/slots/<int:doctor_id>",
    methods=["GET"]
)
@jwt_required()
def get_available_slots(doctor_id):

    # --------------------------------------------------
    # Verify doctor exists
    # --------------------------------------------------

    doctor = Doctor.query.get(doctor_id)

    if not doctor:
        return jsonify({
            "message": "Doctor not found"
        }), 404

    # --------------------------------------------------
    # Get requested date
    # --------------------------------------------------

    date_string = request.args.get("date")

    if not date_string:
        return jsonify({
            "message": "date query parameter is required"
        }), 400

    # --------------------------------------------------
    # Validate date
    #
    # Expected:
    # YYYY-MM-DD
    # --------------------------------------------------

    try:

        requested_date = datetime.strptime(
            date_string,
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):

        return jsonify({
            "message": "date must use YYYY-MM-DD format"
        }), 400

    # --------------------------------------------------
    # Remove expired slot holds
    #
    # This makes expired holds disappear from the
    # availability system.
    # --------------------------------------------------

    now = datetime.now()

    expired_holds = SlotHold.query.filter(
        SlotHold.expires_at <= now
    ).all()

    for expired_hold in expired_holds:
        db.session.delete(expired_hold)

    if expired_holds:
        db.session.flush()

    # --------------------------------------------------
    # Check doctor leave
    # --------------------------------------------------

    doctor_leave = DoctorLeave.query.filter_by(
        doctor_id=doctor.id,
        leave_date=requested_date
    ).first()

    if doctor_leave:

        # Commit removal of expired holds, if any
        db.session.commit()

        return jsonify({
            "doctor_id": doctor.id,
            "date": requested_date.isoformat(),
            "available": False,
            "message": "Doctor is on leave on this date",
            "slots": []
        }), 200

    # --------------------------------------------------
    # Determine day of week
    #
    # Monday = 0
    # Tuesday = 1
    # ...
    # Sunday = 6
    # --------------------------------------------------

    day_of_week = requested_date.weekday()

    # --------------------------------------------------
    # Find working hours
    # --------------------------------------------------

    working_hour = WorkingHour.query.filter_by(
        doctor_id=doctor.id,
        day_of_week=day_of_week
    ).order_by(
        WorkingHour.start_time.asc()
    ).first()

    # --------------------------------------------------
    # Doctor does not work on this day
    # --------------------------------------------------

    if not working_hour:

        db.session.commit()

        return jsonify({
            "doctor_id": doctor.id,
            "date": requested_date.isoformat(),
            "available": False,
            "message": "Doctor is not working on this day",
            "slots": []
        }), 200

    # --------------------------------------------------
    # Generate slots
    # --------------------------------------------------

    slot_duration = working_hour.slot_duration

    if slot_duration <= 0:

        db.session.rollback()

        return jsonify({
            "message": "Invalid slot duration configured for doctor"
        }), 500

    current_datetime = datetime.combine(
        requested_date,
        working_hour.start_time
    )

    end_datetime = datetime.combine(
        requested_date,
        working_hour.end_time
    )

    slots = []

    while current_datetime + timedelta(
        minutes=slot_duration
    ) <= end_datetime:

        slot_start = current_datetime

        slot_end = current_datetime + timedelta(
            minutes=slot_duration
        )

        # --------------------------------------------------
        # Check scheduled appointment
        # --------------------------------------------------

        existing_appointment = Appointment.query.filter_by(
            doctor_id=doctor.id,
            appointment_date=slot_start
        ).filter(
            Appointment.status == "scheduled"
        ).first()

        # --------------------------------------------------
        # Check active slot hold
        # --------------------------------------------------

        existing_hold = SlotHold.query.filter(
            SlotHold.doctor_id == doctor.id,
            SlotHold.appointment_date == slot_start,
            SlotHold.expires_at > now
        ).first()

        # --------------------------------------------------
        # Slot is available only if:
        #
        # No scheduled appointment
        # AND
        # No active hold
        # --------------------------------------------------

        if (
            not existing_appointment
            and not existing_hold
        ):

            slots.append({
                "start_time": slot_start.strftime("%H:%M"),
                "end_time": slot_end.strftime("%H:%M"),
                "available": True
            })

        current_datetime = slot_end

    # --------------------------------------------------
    # Commit removal of expired holds
    # --------------------------------------------------

    db.session.commit()

    # --------------------------------------------------
    # Return generated slots
    # --------------------------------------------------

    return jsonify({
        "doctor_id": doctor.id,
        "date": requested_date.isoformat(),
        "available": len(slots) > 0,
        "working_hours": {
            "start_time": working_hour.start_time.strftime("%H:%M"),
            "end_time": working_hour.end_time.strftime("%H:%M"),
            "slot_duration": working_hour.slot_duration
        },
        "slots": slots
    }), 200