from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.database import db
from backend.models.symptom import Symptom
from backend.models.appointment import Appointment
from backend.models.patient import Patient
from backend.models.doctor import Doctor
from backend.models.ai_summary import AISummary
from backend.services.ai_summary_service import generate_pre_visit_summary


symptom_bp = Blueprint(
    "symptom",
    __name__,
    url_prefix="/api/symptoms"
)


# ==================================================
# POST /api/symptoms/
# Patient submits symptoms
# ==================================================

@symptom_bp.route("/", methods=["POST"])
@jwt_required()
def create_symptom():

    user_id = int(get_jwt_identity())

    # ----------------------------------------------
    # Verify patient
    # ----------------------------------------------

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if not patient:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    # ----------------------------------------------
    # Read request data
    # ----------------------------------------------

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    appointment_id = data.get("appointment_id")
    description = data.get("description")

    if not appointment_id or not description:
        return jsonify({
            "message": "appointment_id and description are required"
        }), 400

    # ----------------------------------------------
    # Validate description
    # ----------------------------------------------

    if not isinstance(description, str):
        return jsonify({
            "message": "description must be a string"
        }), 400

    description = description.strip()

    if not description:
        return jsonify({
            "message": "description cannot be empty"
        }), 400

    # ----------------------------------------------
    # Verify appointment belongs to patient
    # ----------------------------------------------

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        patient_id=patient.id
    ).first()

    if not appointment:
        return jsonify({
            "message": (
                "Appointment not found or does not "
                "belong to you"
            )
        }), 404

    # ==================================================
    # STEP 1 — Store patient symptoms
    # ==================================================

    symptom = Symptom(
        appointment_id=appointment.id,
        description=description
    )

    db.session.add(symptom)

    try:
        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            f"Failed to save patient symptoms: {e}"
        )

        return jsonify({
            "message": "Failed to save symptoms"
        }), 500

    # ==================================================
    # STEP 2 — Generate pre-visit AI summary
    # ==================================================

    try:

        ai_result = generate_pre_visit_summary(
            description
        )

    except Exception as e:

        print(
            f"LLM pre-visit summary generation failed: {e}"
        )

        return jsonify({
            "message": (
                "Symptoms submitted successfully, "
                "but the AI pre-visit summary could "
                "not be generated at this time."
            ),
            "symptom_id": symptom.id,
            "ai_summary_generated": False
        }), 201

    # ==================================================
    # STEP 3 — Validate AI response
    # ==================================================

    required_fields = [
        "urgency_level",
        "chief_complaint",
        "suggested_question_1",
        "suggested_question_2",
        "suggested_question_3"
    ]

    if not all(
        field in ai_result
        for field in required_fields
    ):

        print(
            "Invalid AI response: "
            f"{ai_result}"
        )

        return jsonify({
            "message": (
                "Symptoms were submitted, but the AI "
                "returned an invalid summary."
            ),
            "symptom_id": symptom.id,
            "ai_summary_generated": False
        }), 201

    # ----------------------------------------------
    # Validate urgency
    # ----------------------------------------------

    if ai_result["urgency_level"] not in [
        "Low",
        "Medium",
        "High"
    ]:

        print(
            "Invalid urgency level returned by AI: "
            f"{ai_result['urgency_level']}"
        )

        return jsonify({
            "message": (
                "Symptoms were submitted, but the AI "
                "returned an invalid urgency level."
            ),
            "symptom_id": symptom.id,
            "ai_summary_generated": False
        }), 201

    # ==================================================
    # STEP 4 — Check whether summary already exists
    # ==================================================

    existing_summary = AISummary.query.filter_by(
        appointment_id=appointment.id
    ).first()

    if existing_summary:

        return jsonify({
            "message": (
                "Symptoms were submitted successfully, "
                "but a pre-visit AI summary already exists "
                "for this appointment."
            ),
            "symptom_id": symptom.id,
            "ai_summary_id": existing_summary.id,
            "ai_summary_generated": True
        }), 201

    # ==================================================
    # STEP 5 — Store AI summary in PostgreSQL
    # ==================================================

    ai_summary = AISummary(
        appointment_id=appointment.id,
        urgency_level=ai_result["urgency_level"],
        chief_complaint=ai_result["chief_complaint"],
        suggested_question_1=(
            ai_result["suggested_question_1"]
        ),
        suggested_question_2=(
            ai_result["suggested_question_2"]
        ),
        suggested_question_3=(
            ai_result["suggested_question_3"]
        )
    )

    db.session.add(ai_summary)

    try:

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print(
            f"Failed to save AI summary: {e}"
        )

        return jsonify({
            "message": (
                "Symptoms were saved, but the AI "
                "summary could not be stored."
            ),
            "symptom_id": symptom.id,
            "ai_summary_generated": False
        }), 500

    # ==================================================
    # STEP 6 — Return successful response
    # ==================================================

    return jsonify({
        "message": (
            "Symptoms and pre-visit AI summary "
            "saved successfully"
        ),
        "symptom_id": symptom.id,
        "ai_summary_id": ai_summary.id,
        "ai_summary_generated": True,
        "ai_summary": {
            "urgency_level": (
                ai_summary.urgency_level
            ),
            "chief_complaint": (
                ai_summary.chief_complaint
            ),
            "suggested_question_1": (
                ai_summary.suggested_question_1
            ),
            "suggested_question_2": (
                ai_summary.suggested_question_2
            ),
            "suggested_question_3": (
                ai_summary.suggested_question_3
            )
        }
    }), 201


# ==================================================
# GET /api/symptoms/appointment/<appointment_id>
#
# Doctor views:
#   1. Patient symptoms
#   2. AI pre-visit summary
# ==================================================

@symptom_bp.route(
    "/appointment/<int:appointment_id>",
    methods=["GET"]
)
@jwt_required()
def get_appointment_symptoms(appointment_id):

    user_id = int(get_jwt_identity())

    # ----------------------------------------------
    # Verify doctor
    # ----------------------------------------------

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    if not doctor:
        return jsonify({
            "message": "Doctor profile not found"
        }), 404

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
                "Appointment not found or does not "
                "belong to you"
            )
        }), 404

    # ----------------------------------------------
    # Get patient symptoms
    # ----------------------------------------------

    symptoms = Symptom.query.filter_by(
        appointment_id=appointment.id
    ).order_by(
        Symptom.created_at.asc()
    ).all()

    symptom_result = []

    for symptom in symptoms:

        symptom_result.append({
            "id": symptom.id,
            "appointment_id": symptom.appointment_id,
            "description": symptom.description,
            "created_at": symptom.created_at.isoformat()
        })

    # ----------------------------------------------
    # Get AI pre-visit summary
    # ----------------------------------------------

    ai_summary = AISummary.query.filter_by(
        appointment_id=appointment.id
    ).first()

    # ----------------------------------------------
    # Build AI summary response
    # ----------------------------------------------

    ai_summary_result = None

    if ai_summary:

        ai_summary_result = {
            "id": ai_summary.id,
            "appointment_id": ai_summary.appointment_id,
            "urgency_level": ai_summary.urgency_level,
            "chief_complaint": ai_summary.chief_complaint,
            "suggested_question_1": (
                ai_summary.suggested_question_1
            ),
            "suggested_question_2": (
                ai_summary.suggested_question_2
            ),
            "suggested_question_3": (
                ai_summary.suggested_question_3
            ),
            "created_at": (
                ai_summary.created_at.isoformat()
            ),
            "updated_at": (
                ai_summary.updated_at.isoformat()
            )
        }

    # ----------------------------------------------
    # Return symptoms + AI summary
    # ----------------------------------------------

    return jsonify({
        "appointment_id": appointment.id,
        "symptoms": symptom_result,
        "ai_summary": ai_summary_result
    }), 200