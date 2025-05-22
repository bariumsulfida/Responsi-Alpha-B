from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)

# PostgreSQL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/rspns'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

HOST_IP = "192.168.137.19"
db = SQLAlchemy(app)
socketio = SocketIO(app)

def timestamp():
    now = datetime.now()
    return f"{now.day} - {now.month} - {now.year} {now.hour:02d}:{now.minute:02d}:{now.second:02d}"

# Define the SensorData model
class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    id = db.Column(db.BigInteger, primary_key=True)
    temp = db.Column(db.Numeric(6, 3))
    humidity = db.Column(db.Numeric(5, 2))
    illuminance = db.Column(db.REAL)
    co2 = db.Column(db.Integer)
    noise = db.Column(db.Numeric(5, 2))
    current = db.Column(db.Numeric(7, 4))
    voltage = db.Column(db.Numeric(7, 4))
    gas_detection = db.Column(db.Boolean)
    earthquake = db.Column(db.Boolean)
    time = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

# Define the PeopleCount model
class PeopleCount(db.Model):
    __tablename__ = 'people_count'
    id = db.Column(db.BigInteger, primary_key=True)
    jumlah_orang = db.Column(db.BigInteger)
    time = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now())

@app.route('/', methods=['GET'])
def get_sensor_data():
    sensors = SensorData.query.all()
    people_counts = PeopleCount.query.all()
    return render_template('index.html', sensors=sensors, people_counts=people_counts)

# Route to get all sensor data
@app.route('/api/', methods=['GET'])
def api_get_sensor_data():
    sensors = SensorData.query.all()
    sensor_list = [{
        "id": sensor.id,
        "temp": float(sensor.temp) if sensor.temp else None,
        "humidity": float(sensor.humidity) if sensor.humidity else None,
        "illuminance": float(sensor.illuminance) if sensor.illuminance else None,
        "co2": sensor.co2,
        "noise": float(sensor.noise) if sensor.noise else None,
        "current": float(sensor.current) if sensor.current else None,
        "voltage": float(sensor.voltage) if sensor.voltage else None,
        "gas_detection": sensor.gas_detection,
        "earthquake": sensor.earthquake,
        "time": sensor.time.isoformat() if sensor.time else None,
    } for sensor in sensors]
    
    people_counts = PeopleCount.query.all()
    people_list = [{
        "id": count.id,
        "jumlah_orang": count.jumlah_orang,
        "time": count.time.isoformat() if count.time else None
    } for count in people_counts]
    
    return jsonify({"sensor_data": sensor_list, "people_counts": people_list})

# Route to add new sensor data (POST)
@app.route('/api/send', methods=['POST'])
def add_sensor_data():
    data = request.get_json()
    
    required_fields = [
        'temp', 'humidity', 'illuminance', 'co2', 'noise',
        'current', 'voltage', 'gas_detection', 'earthquake'
    ]
    
    if not all(key in data for key in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    new_sensor = SensorData(
        temp=data['temp'],
        humidity=data['humidity'],
        illuminance=data['illuminance'],
        co2=data['co2'],
        noise=data['noise'],
        current=data['current'],
        voltage=data['voltage'],
        gas_detection=data['gas_detection'],
        earthquake=data['earthquake']
    )

    try:
        db.session.add(new_sensor)
        db.session.commit()
        send_sensor_data()
        return jsonify({"message": "Sensor data added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route to add people count data
@app.route('/api/people', methods=['POST'])
def add_people_count():
    data = request.get_json()
    
    if 'jumlah_orang' not in data:
        return jsonify({"error": "Missing jumlah_orang field"}), 400

    new_count = PeopleCount(
        jumlah_orang=data['jumlah_orang']
    )

    try:
        db.session.add(new_count)
        db.session.commit()
        send_people_count()
        return jsonify({"message": "People count added successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def send_sensor_data():
    latest_sensor = SensorData.query.order_by(SensorData.time.desc()).first()
    
    sensor_list = []
    if latest_sensor:
        sensor_list.append({
            "id": latest_sensor.id,
            "temp": float(latest_sensor.temp) if latest_sensor.temp else None,
            "humidity": float(latest_sensor.humidity) if latest_sensor.humidity else None,
            "illuminance": float(latest_sensor.illuminance) if latest_sensor.illuminance else None,
            "co2": latest_sensor.co2,
            "noise": float(latest_sensor.noise) if latest_sensor.noise else None,
            "current": float(latest_sensor.current) if latest_sensor.current else None,
            "voltage": float(latest_sensor.voltage) if latest_sensor.voltage else None,
            "gas_detection": latest_sensor.gas_detection,
            "earthquake": latest_sensor.earthquake,
            "time": latest_sensor.time.isoformat() if latest_sensor.time else None,
            "timestamp": timestamp()
        })
    socketio.emit('sensor_data', sensor_list)

def send_people_count():
    latest_count = PeopleCount.query.order_by(PeopleCount.time.desc()).first()
    
    count_data = []
    if latest_count:
        count_data.append({
            "id": latest_count.id,
            "jumlah_orang": latest_count.jumlah_orang,
            "time": latest_count.time.isoformat() if latest_count.time else None,
            "timestamp": timestamp()
        })
    socketio.emit('people_count', count_data)

# WebSocket connection handlers
@socketio.on('connect')
def handle_connect():
    send_sensor_data()
    send_people_count()

if __name__ == '__main__':
    socketio.run(app, host=HOST_IP, debug=True, port=5000)