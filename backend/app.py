from flask import Flask
from flask_jwt_extended import JWTManager

from backend.config.config import Config
from database.database import db

# --------------------------------------------------
# Models
# --------------------------------------------------

from backend.models.user import User
from backend.models.patient import Patient
from backend.models.doctor import Doctor
from backend.models.appointment import Appointment
from backend.models.symptom import Symptom
from backend.models.follow_up import FollowUp
from backend.models.reminder import Reminder
from backend.models.notification import Notification
from backend.models.consultation import Consultation
from backend.models.prescription import Prescription
from backend.models.medication import Medication
from backend.models.working_hour import WorkingHour
from backend.models.doctor_leave import DoctorLeave
from backend.models.slot_hold import SlotHold
from backend.models.ai_summary import AISummary
# --------------------------------------------------
# Routes
# --------------------------------------------------

from backend.routes.auth_routes import auth_bp
from backend.routes.doctor_routes import doctor_bp
from backend.routes.appointment_routes import appointment_bp
from backend.routes.symptom_routes import symptom_bp
from backend.routes.follow_up_routes import follow_up_bp
from backend.routes.notification_routes import notification_bp
from backend.routes.reminder_routes import reminder_bp
from backend.routes.consultation_routes import consultation_bp
from backend.routes.prescription_routes import prescription_bp
from backend.routes.availability_routes import availability_bp
# --------------------------------------------------
# Services
# --------------------------------------------------

from backend.services.reminder_scheduler import start_scheduler


# --------------------------------------------------
# Flask Application
# --------------------------------------------------

app = Flask(__name__)

# Load application configuration
app.config.from_object(Config)

# JWT configuration
jwt = JWTManager(app)

# Initialize SQLAlchemy
db.init_app(app)


# --------------------------------------------------
# Create database tables
# --------------------------------------------------
#
# This creates any tables defined by the imported
# SQLAlchemy models that do not already exist.
#
# Existing tables and data are NOT deleted.
# --------------------------------------------------

with app.app_context():
    db.create_all()


# --------------------------------------------------
# Register Blueprints
# --------------------------------------------------

app.register_blueprint(auth_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(appointment_bp)
app.register_blueprint(symptom_bp)
app.register_blueprint(follow_up_bp)
app.register_blueprint(notification_bp)
app.register_blueprint(reminder_bp)
app.register_blueprint(consultation_bp)
app.register_blueprint(prescription_bp)
app.register_blueprint(availability_bp)

# --------------------------------------------------
# Start Reminder Scheduler
# --------------------------------------------------

start_scheduler(app)


# --------------------------------------------------
# Home Route
# --------------------------------------------------

@app.route("/")
def home():
    return "Healthcare Appointment & Follow-up Manager API is running!"


# --------------------------------------------------
# Run Application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)