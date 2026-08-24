from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database.database import db
from backend.models.prescription import Prescription
from backend.models.medication import Medication
from backend.models.appointment import Appointment
from backend.models.consultation import Consultation
from backend.models.doctor import Doctor
from backend.models.patient import Patient


# --------------------------------------------------
# Blueprint
# --------------------------------------------------

prescription_bp = Blueprint(
    "prescription",
    __name__,
    url_prefix="/api/prescriptions"
)


# --------------------------------------------------
# POST /api/prescriptions/
# Doctor creates one prescription with
# multiple medications
# --------------------------------------------------

@prescription_bp.route("/", methods=["POST"])
@jwt_required()
def create_prescription():

    user_id = int(get_jwt_identity())

    # --------------------------------------------------
    # Verify doctor
    # --------------------------------------------------

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    if not doctor:
        return jsonify({
            "message": "Only doctors can create prescriptions"
        }), 403

    # --------------------------------------------------
    # Get request data
    # --------------------------------------------------

    data = request.get_json()

    if not data:
        return jsonify({
            "message": "Request body is required"
        }), 400

    appointment_id = data.get("appointment_id")
    instructions = data.get("instructions")
    medications = data.get("medications")

    # --------------------------------------------------
    # Validate appointment_id
    # --------------------------------------------------

    if not appointment_id:
        return jsonify({
            "message": "appointment_id is required"
        }), 400

    # --------------------------------------------------
    # Validate medications
    # --------------------------------------------------

    if not medications:
        return jsonify({
            "message": "medications is required"
        }), 400

    if not isinstance(medications, list):
        return jsonify({
            "message": "medications must be an array"
        }), 400

    if len(medications) == 0:
        return jsonify({
            "message": "At least one medication is required"
        }), 400

    # --------------------------------------------------
    # Verify appointment belongs to this doctor
    # --------------------------------------------------

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

    # --------------------------------------------------
    # Verify consultation exists
    # --------------------------------------------------

    consultation = Consultation.query.filter_by(
        appointment_id=appointment.id
    ).first()

    if not consultation:
        return jsonify({
            "message": (
                "Consultation must be created before "
                "a prescription"
            )
        }), 400

    # --------------------------------------------------
    # Validate each medication
    # --------------------------------------------------

    for medication in medications:

        if not isinstance(medication, dict):
            return jsonify({
                "message": (
                    "Each medication must be an object"
                )
            }), 400

        medicine_name = medication.get("medicine_name")
        frequency = medication.get("frequency")

        if not medicine_name:
            return jsonify({
                "message": (
                    "medicine_name is required for "
                    "every medication"
                )
            }), 400

        if not frequency:
            return jsonify({
                "message": (
                    "frequency is required for "
                    "every medication"
                )
            }), 400

    # --------------------------------------------------
    # Create ONE prescription
    # --------------------------------------------------

    prescription = Prescription(
        appointment_id=appointment.id,
        doctor_id=doctor.id,
        patient_id=appointment.patient_id,
        instructions=instructions
    )

    db.session.add(prescription)

    # Flush so prescription.id becomes available
    # before creating medications
    db.session.flush()

    # --------------------------------------------------
    # Create MULTIPLE medications
    # --------------------------------------------------

    medication_response = []

    # Use appointment start time as the medication
    # start date when available.
    start_date = appointment.appointment_date

    for medication_data in medications:

        medicine_name = medication_data.get(
            "medicine_name"
        )

        dosage = medication_data.get("dosage")

        frequency = medication_data.get(
            "frequency"
        )

        duration = medication_data.get(
            "duration"
        )

        # --------------------------------------------------
        # Calculate end date from duration
        # --------------------------------------------------

        end_date = None

        if duration:
            try:
                duration_number = int(
                    duration.split()[0]
                )

                end_date = start_date + timedelta(
                    days=duration_number
                )

            except (ValueError, IndexError):
                end_date = None

        medication = Medication(
            prescription_id=prescription.id,
            medicine_name=medicine_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            start_date=start_date,
            end_date=end_date
        )

        db.session.add(medication)

        medication_response.append({
            "medicine_name": medicine_name,
            "dosage": dosage,
            "frequency": frequency,
            "duration": duration,
            "start_date": start_date.isoformat(),
            "end_date": (
                end_date.isoformat()
                if end_date
                else None
            )
        })

    # --------------------------------------------------
    # Save everything
    # --------------------------------------------------

    db.session.commit()

    # --------------------------------------------------
    # Return response
    # --------------------------------------------------

    return jsonify({
        "message": "Prescription created successfully",
        "prescription_id": prescription.id,
        "appointment_id": prescription.appointment_id,
        "doctor_id": prescription.doctor_id,
        "patient_id": prescription.patient_id,
        "instructions": prescription.instructions,
        "medications": medication_response
    }), 201


# --------------------------------------------------
# GET /api/prescriptions/<prescription_id>
# Doctor views a prescription with all medications
# --------------------------------------------------

@prescription_bp.route(
    "/<int:prescription_id>",
    methods=["GET"]
)
@jwt_required()
def get_prescription(prescription_id):

    user_id = int(get_jwt_identity())

    # --------------------------------------------------
    # Verify doctor
    # --------------------------------------------------

    doctor = Doctor.query.filter_by(
        user_id=user_id
    ).first()

    if not doctor:
        return jsonify({
            "message": "Only doctors can view this prescription"
        }), 403

    # --------------------------------------------------
    # Find prescription
    # --------------------------------------------------

    prescription = Prescription.query.get(
        prescription_id
    )

    if not prescription:
        return jsonify({
            "message": "Prescription not found"
        }), 404

    # --------------------------------------------------
    # Verify prescription belongs to doctor
    # --------------------------------------------------

    if prescription.doctor_id != doctor.id:
        return jsonify({
            "message": (
                "You are not authorized to view "
                "this prescription"
            )
        }), 403

    # --------------------------------------------------
    # Get medications
    # --------------------------------------------------

    medications = Medication.query.filter_by(
        prescription_id=prescription.id
    ).all()

    medication_response = []

    for medication in medications:

        medication_response.append({
            "id": medication.id,
            "medicine_name": medication.medicine_name,
            "dosage": medication.dosage,
            "frequency": medication.frequency,
            "duration": medication.duration,
            "start_date": (
                medication.start_date.isoformat()
                if medication.start_date
                else None
            ),
            "end_date": (
                medication.end_date.isoformat()
                if medication.end_date
                else None
            ),
            "created_at": (
                medication.created_at.isoformat()
                if medication.created_at
                else None
            )
        })

    # --------------------------------------------------
    # Return prescription
    # --------------------------------------------------

    return jsonify({
        "id": prescription.id,
        "appointment_id": prescription.appointment_id,
        "doctor_id": prescription.doctor_id,
        "patient_id": prescription.patient_id,
        "instructions": prescription.instructions,
        "created_at": (
            prescription.created_at.isoformat()
            if prescription.created_at
            else None
        ),
        "medications": medication_response
    }), 200
 
 
# --------------------------------------------------
# GET /api/prescriptions/patient
# Patient views all of their prescriptions
# --------------------------------------------------

@prescription_bp.route(
    "/patient",
    methods=["GET"]
)
@jwt_required()
def get_patient_prescriptions():

    user_id = int(get_jwt_identity())

    # --------------------------------------------------
    # Verify patient
    # --------------------------------------------------

    patient = Patient.query.filter_by(
        user_id=user_id
    ).first()

    if not patient:
        return jsonify({
            "message": "Patient profile not found"
        }), 404

    # --------------------------------------------------
    # Get patient's prescriptions
    # --------------------------------------------------

    prescriptions = Prescription.query.filter_by(
        patient_id=patient.id
    ).order_by(
        Prescription.created_at.desc()
    ).all()

    result = []

    # --------------------------------------------------
    # Add medications for every prescription
    # --------------------------------------------------

    for prescription in prescriptions:

        medications = Medication.query.filter_by(
            prescription_id=prescription.id
        ).all()

        medication_response = []

        for medication in medications:

            medication_response.append({
                "id": medication.id,
                "medicine_name": medication.medicine_name,
                "dosage": medication.dosage,
                "frequency": medication.frequency,
                "duration": medication.duration,
                "start_date": (
                    medication.start_date.isoformat()
                    if medication.start_date
                    else None
                ),
                "end_date": (
                    medication.end_date.isoformat()
                    if medication.end_date
                    else None
                ),
                "created_at": (
                    medication.created_at.isoformat()
                    if medication.created_at
                    else None
                )
            })

        result.append({
            "id": prescription.id,
            "appointment_id": prescription.appointment_id,
            "doctor_id": prescription.doctor_id,
            "patient_id": prescription.patient_id,
            "instructions": prescription.instructions,
            "created_at": (
                prescription.created_at.isoformat()
                if prescription.created_at
                else None
            ),
            "medications": medication_response
        })

    return jsonify(result), 200
