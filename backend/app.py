from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config.config import Config


app = Flask(__name__)

# Load application configuration
app.config.from_object(Config)

# Initialize database
db = SQLAlchemy(app)


@app.route("/")
def home():
    return "Healthcare Appointment & Follow-up Manager API is running!"


if __name__ == "__main__":
    app.run(debug=True)