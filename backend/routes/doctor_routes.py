from flask import Blueprint, jsonify

from backend.models.doctor import Doctor
from backend.models.user import User


doctor_bp = Blueprint("doctor", __name__, url_prefix="/api/doctors")


@doctor_bp.route("/", methods=["GET"])
def get_doctors():
    doctors = Doctor.query.all()

    result = []

    for doctor in doctors:
        user = User.query.get(doctor.user_id)

        result.append({
            "id": doctor.id,
            "name": user.name if user else None,
            "email": user.email if user else None,
            "specialization": doctor.specialization,
            "license_number": doctor.license_number,
            "phone": doctor.phone
        })

    return jsonify(result), 200