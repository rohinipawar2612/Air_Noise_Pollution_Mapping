from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pollution_secret_key_123'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "pollution.db")

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    if user_id == "1":
        return User("1", ADMIN_USERNAME)
    return None

def get_db():
    conn = sqlite3.connect(
        DATABASE,
        timeout=10,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noise_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            noise_level REAL NOT NULL,
            source TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS air_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            aqi REAL NOT NULL,
            pm25 REAL NOT NULL,
            air_quality TEXT NOT NULL,
            source TEXT NOT NULL,
            data_type TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            user = User("1", ADMIN_USERNAME)
            login_user(user)
            return redirect(url_for("data_collection"))
        else:
            return """
            <script>
                alert("❌ Invalid Admin Credentials!");
                window.location.href = "/login";
            </script>
            """
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM noise_data
        ORDER BY id DESC
    """)
    noise_records = cursor.fetchall()
    cursor.execute("""
        SELECT *
        FROM air_data
        ORDER BY id DESC
    """)
    air_records = cursor.fetchall()
    conn.close()
    return render_template(
        "dashboard.html",
        noise_records=noise_records,
        air_records=air_records
    )

@app.route("/map")
def pollution_map():
    return render_template("map.html")

@app.route("/api/pollution")
def pollution_api():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, location, latitude, longitude, noise_level, source, date, time
        FROM noise_data
        ORDER BY id DESC
    """)
    noise_rows = cursor.fetchall()
    cursor.execute("""
        SELECT id, location, latitude, longitude, aqi, pm25, air_quality, source, data_type, date, time
        FROM air_data
        ORDER BY id DESC
    """)
    air_rows = cursor.fetchall()
    noise_data = [dict(row) for row in noise_rows]
    air_data = [dict(row) for row in air_rows]
    conn.close()
    return jsonify({
        "noise": noise_data,
        "air": air_data
    })

@app.route("/data-collection")
@login_required
def data_collection():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM noise_data
        ORDER BY id DESC
    """)
    noise_records = cursor.fetchall()
    cursor.execute("""
        SELECT *
        FROM air_data
        ORDER BY id DESC
    """)
    air_records = cursor.fetchall()
    conn.close()
    return render_template(
        "data_collection.html",
        records=noise_records,
        air_records=air_records
    )

@app.route("/add-noise", methods=["POST"])
@login_required
def add_noise():
    location = request.form.get("location")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    noise_level = request.form.get("noise_level")
    source = request.form.get("source")
    date = request.form.get("date")
    time = request.form.get("time")
    if not all([location, latitude, longitude, noise_level, source, date, time]):
        return "❌ Please fill all Noise Data fields."
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO noise_data
            (location, latitude, longitude, noise_level, source, date, time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            location,
            float(latitude),
            float(longitude),
            float(noise_level),
            source,
            date,
            time
        ))
        conn.commit()
        conn.close()
        return """
        <script>
            alert("✅ Noise data saved successfully!");
            window.location.href = "/data-collection";
        </script>
        """
    except Exception as e:
        return f"❌ Error saving Noise Data: {e}"

@app.route("/add-air", methods=["POST"])
@login_required
def add_air():
    location = request.form.get("location")
    latitude = request.form.get("latitude")
    longitude = request.form.get("longitude")
    aqi = request.form.get("aqi")
    pm25 = request.form.get("pm25")
    air_quality = request.form.get("air_quality")
    source = request.form.get("source")
    data_type = request.form.get("data_type")
    date = request.form.get("date")
    time = request.form.get("time")
    if not all([location, latitude, longitude, aqi, pm25, air_quality, source, data_type, date, time]):
        return "❌ Please fill all Air Data fields."
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO air_data
            (location, latitude, longitude, aqi, pm25, air_quality, source, data_type, date, time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            location,
            float(latitude),
            float(longitude),
            float(aqi),
            float(pm25),
            air_quality,
            source,
            data_type,
            date,
            time
        ))
        conn.commit()
        conn.close()
        return """
        <script>
            alert("✅ Air data saved successfully!");
            window.location.href = "/data-collection";
        </script>
        """
    except Exception as e:
        return f"❌ Error saving Air Data: {e}"

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
