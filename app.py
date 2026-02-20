import os
import math
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

fernet = Fernet(os.getenv("FERNET_KEY").encode())

# ----------------------------
# Models
# ----------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(50))  # admin / clinician

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    encrypted_name = db.Column(db.Text)
    dob = db.Column(db.Date)
    sex = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Functional
    gait_speed = db.Column(db.Float)
    grip_strength = db.Column(db.Float)
    tug_time = db.Column(db.Float)

    # Cognitive
    moca_score = db.Column(db.Integer)

    # Mental
    phq9 = db.Column(db.Integer)
    gad7 = db.Column(db.Integer)

    # Cardio
    sbp = db.Column(db.Float)
    total_chol = db.Column(db.Float)
    smoker = db.Column(db.Boolean)

    # Labs
    hba1c = db.Column(db.Float)
    ldl = db.Column(db.Float)
    egfr = db.Column(db.Float)

    # QoL
    whoqol = db.Column(db.Float)

    # AI Outputs
    healthspan_index = db.Column(db.Float)
    ai_confidence = db.Column(db.Float)

    consent = db.Column(db.Boolean)
    cohort_flag = db.Column(db.Boolean)

# ----------------------------
# Encryption helpers
# ----------------------------

def encrypt(text):
    return fernet.encrypt(text.encode()).decode()

def decrypt(token):
    return fernet.decrypt(token.encode()).decode()

# ----------------------------
# Healthspan Index Algorithm
# ----------------------------

def calculate_healthspan(data):
    score = 0

    # Functional
    score += min(data["gait_speed"] / 1.2, 1) * 15
    score += min(data["grip_strength"] / 35, 1) * 10
    score += (1 - min(data["tug_time"] / 20, 1)) * 10

    # Cognitive
    score += (data["moca_score"] / 30) * 15

    # Mental
    score += (1 - data["phq9"] / 27) * 10
    score += (1 - data["gad7"] / 21) * 5

    # Cardio
    score += (1 - min(data["sbp"] / 180, 1)) * 10
    score += (1 - min(data["hba1c"] / 10, 1)) * 10

    # QoL
    score += (data["whoqol"] / 100) * 15

    return round(score, 2)

def calculate_confidence(data):
    filled = sum(1 for v in data.values() if v is not None)
    total = len(data)
    return round((filled / total) * 100, 2)

# ----------------------------
# Routes
# ----------------------------

@app.route("/create_patient", methods=["POST"])
def create_patient():
    data = request.json
    patient = Patient(
        encrypted_name=encrypt(data["name"]),
        dob=datetime.strptime(data["dob"], "%Y-%m-%d"),
        sex=data["sex"]
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify({"message": "Patient created"}), 201

@app.route("/new_assessment/<int:patient_id>", methods=["POST"])
def new_assessment(patient_id):
    data = request.json

    healthspan = calculate_healthspan(data)
    confidence = calculate_confidence(data)

    assessment = Assessment(
        patient_id=patient_id,
        gait_speed=data["gait_speed"],
        grip_strength=data["grip_strength"],
        tug_time=data["tug_time"],
        moca_score=data["moca_score"],
        phq9=data["phq9"],
        gad7=data["gad7"],
        sbp=data["sbp"],
        total_chol=data["total_chol"],
        smoker=data["smoker"],
        hba1c=data["hba1c"],
        ldl=data["ldl"],
        egfr=data["egfr"],
        whoqol=data["whoqol"],
        healthspan_index=healthspan,
        ai_confidence=confidence,
        consent=data["consent"],
        cohort_flag=data.get("cohort_flag", False)
    )

    db.session.add(assessment)
    db.session.commit()

    return jsonify({
        "healthspan_index": healthspan,
        "ai_confidence": confidence
    })

@app.route("/dashboard")
def dashboard():
    avg_score = db.session.query(
        db.func.avg(Assessment.healthspan_index)
    ).scalar()
    return jsonify({"population_avg_healthspan": round(avg_score or 0,2)})

@app.route("/backup")
def backup():
    os.system("pg_dump $DATABASE_URL > backup.sql")
    return jsonify({"message": "Backup triggered"})

# ----------------------------
# Run (Production ready)
# ----------------------------

if __name__ == "__main__":
    app.run()
