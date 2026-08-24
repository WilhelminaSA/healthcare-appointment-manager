from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.database import db
from backend.models.consultation import Consultation
from backend.models.appointment import Appointment
from backend.models.doctor import Doctor


consultation_bp = Blueprint(
    "consultation",
    __name__,
    url_prefix="/api/consultations"
)


# --------------------------------------------------
# POST /api/consultations/
# Doctor submits post-visit consultation notes
# --------------------------------------------------

@consultation_bp.route("/", methods=["POST"])
@jwt_required()
def create_consultation():

    user_id = int(get_jwt_identity())

    # ----------------------------------------------
    # Verify doctor
    # ----------------------------------------------

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    if not doctor:
        return jsonify({
            "message": "Only doctors can submit consultations"
        }), 403

    data = request.get_json()

    appointment_id = data.get("appointment_id")
    notes = data.get("notes")

    if not appointment_id or not notes:
        return jsonify({
            "message": "appointment_id and notes are required"
        }), 400

    # ----------------------------------------------
    # Verify appointment belongs to this doctor
    # ----------------------------------------------

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        doctor_id=doctor.id
    ).first()

    if not appointment:
        return jsonify({
            "message": (
                "Appointment not found or does not belong "
                "to this doctor"
            )
        }), 404

    # ----------------------------------------------
    # Prevent duplicate consultation
    # ----------------------------------------------

    existing_consultation = Consultation.query.filter_by(
        appointment_id=appointment.id
    ).first()

    if existing_consultation:
        return jsonify({
            "message": "Consultation already exists for this appointment"
        }), 409

    # ----------------------------------------------
    # Create consultation
    # ----------------------------------------------

    consultation = Consultation(
        appointment_id=appointment.id,
        doctor_id=doctor.id,
        notes=notes
    )

    db.session.add(consultation)

    # Mark appointment as completed
    appointment.status = "completed"

    db.session.commit()

    return jsonify({
        "message": "Consultation created successfully",
        "consultation_id": consultation.id,
        "appointment_id": appointment.id
    }), 201


# --------------------------------------------------
# GET /api/consultations/<consultation_id>
# View consultation
# --------------------------------------------------

@consultation_bp.route(
    "/<int:consultation_id>",
    methods=["GET"]
)
@jwt_required()
def get_consultation(consultation_id):

    user_id = int(get_jwt_identity())

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    if not doctor:
        return jsonify({
            "message": "Doctor profile not found"
        }), 404

    consultation = Consultation.query.get(
        consultation_id
    )

    if not consultation:
        return jsonify({
            "message": "Consultation not found"
        }), 404

    if consultation.doctor_id != doctor.id:
        return jsonify({
            "message": "You are not authorized to view this consultation"
        }), 403

    return jsonify({
        "id": consultation.id,
        "appointment_id": consultation.appointment_id,
        "doctor_id": consultation.doctor_id,
        "notes": consultation.notes,
        "created_at": consultation.created_at.isoformat(),
        "updated_at": consultation.updated_at.isoformat()
    }), 200