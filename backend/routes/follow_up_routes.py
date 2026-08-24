from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.database import db
from backend.models.follow_up import FollowUp
from backend.models.appointment import Appointment
from backend.models.patient import Patient
from backend.models.doctor import Doctor


follow_up_bp = Blueprint(
    "follow_up",
    __name__,
    url_prefix="/api/follow-ups"
)


# --------------------------------------------------
# POST /api/follow-ups/
# Doctor creates a follow-up
# --------------------------------------------------

@follow_up_bp.route("/", methods=["POST"])
@jwt_required()
def create_follow_up():

    user_id = int(get_jwt_identity())

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    if not doctor:
        return jsonify({
            "message": "Doctor profile not found"
        }), 404

    data = request.get_json()

    appointment_id = data.get("appointment_id")
    follow_up_date = data.get("follow_up_date")
    notes = data.get("notes")

    if not appointment_id:
        return jsonify({
            "message": "appointment_id is required"
        }), 400

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()

    if not appointment:
        return jsonify({
            "message": "Appointment not found or does not belong to you"
        }), 404

    parsed_date = None

    if follow_up_date:
        try:
            parsed_date = datetime.fromisoformat(
                follow_up_date
            )
        except ValueError:
            return jsonify({
                "message": "Invalid follow_up_date format. "
                           "Use YYYY-MM-DDTHH:MM:SS"
            }), 400

    follow_up = FollowUp(
        appointment_id=appointment.id,
        follow_up_date=parsed_date,
        notes=notes,
        status="pending"
    )

    db.session.add(follow_up)
    db.session.commit()

    return jsonify({
        "message": "Follow-up created successfully",
        "follow_up_id": follow_up.id
    }), 201


# --------------------------------------------------
# GET /api/follow-ups/
# Patient views their follow-ups
# --------------------------------------------------

@follow_up_bp.route("/", methods=["GET"])
@jwt_required()
def get_my_follow_ups():

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
    ).all()

    appointment_ids = [
        appointment.id
        for appointment in appointments
    ]

    follow_ups = FollowUp.query.filter(
        FollowUp.appointment_id.in_(appointment_ids)
    ).all() if appointment_ids else []

    result = []

    for follow_up in follow_ups:
        result.append({
            "id": follow_up.id,
            "appointment_id": follow_up.appointment_id,
            "follow_up_date": (
                follow_up.follow_up_date.isoformat()
                if follow_up.follow_up_date
                else None
            ),
            "notes": follow_up.notes,
            "status": follow_up.status,
            "created_at": follow_up.created_at.isoformat()
        })

    return jsonify(result), 200