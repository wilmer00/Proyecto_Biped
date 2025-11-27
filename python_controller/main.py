from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import time
from threading import Lock
import random

app = Flask(__name__)
CORS(app)

# Estado global de los servos (6 servos)
servo_state = {
    'servo1': {'angle': 90, 'kp': 1.0, 'ki': 0.0, 'kd': 0.0},
    'servo2': {'angle': 90, 'kp': 1.0, 'ki': 0.0, 'kd': 0.0},
    'servo3': {'angle': 90, 'kp': 1.0, 'ki': 0.0, 'kd': 0.0},
    'servo4': {'angle': 90, 'kp': 1.0, 'ki': 0.0, 'kd': 0.0},
    'servo5': {'angle': 90, 'kp': 1.0, 'ki': 0.0, 'kd': 0.0},
    'servo6': {'angle': 90, 'kp': 1.0, 'ki': 0.0, 'kd': 0.0}
}

# Variables para la cámara WebSocket
camera_available = False
camera_url = "ws://localhost:8765"  # URL del WebSocket de Python

state_lock = Lock()

# Endpoint para obtener el estado de todos los servos
@app.route('/api/servos', methods=['GET'])
def get_servos():
    with state_lock:
        return jsonify(servo_state)

# Endpoint para actualizar un servo específico
@app.route('/api/servo/<servo_id>', methods=['POST'])
def update_servo(servo_id):
    if servo_id not in servo_state:
        return jsonify({'error': 'Servo no encontrado'}), 404
    
    data = request.json
    with state_lock:
        if 'angle' in data:
            servo_state[servo_id]['angle'] = max(0, min(180, data['angle']))
        if 'kp' in data:
            servo_state[servo_id]['kp'] = data['kp']
        if 'ki' in data:
            servo_state[servo_id]['ki'] = data['ki']
        if 'kd' in data:
            servo_state[servo_id]['kd'] = data['kd']
    
    return jsonify(servo_state[servo_id])

# Endpoint para actualizar múltiples servos (movimiento de piernas)
@app.route('/api/servos/batch', methods=['POST'])
def update_servos_batch():
    data = request.json
    with state_lock:
        for servo_id, values in data.items():
            if servo_id in servo_state:
                if 'angle' in values:
                    servo_state[servo_id]['angle'] = max(0, min(180, values['angle']))
                if 'kp' in values:
                    servo_state[servo_id]['kp'] = values['kp']
                if 'ki' in values:
                    servo_state[servo_id]['ki'] = values['ki']
                if 'kd' in values:
                    servo_state[servo_id]['kd'] = values['kd']
    
    return jsonify(servo_state)

# Comando de movimiento (W, S, A, D, etc.)
@app.route('/api/command', methods=['POST'])
def command():
    data = request.json
    cmd = data.get('command', '').upper()
    
    # Simular movimientos de piernas según el comando
    movements = {
        'W': {  # Avanzar
            'servo1': {'angle': 110}, 'servo2': {'angle': 70},
            'servo3': {'angle': 100}, 'servo4': {'angle': 80},
            'servo5': {'angle': 95}, 'servo6': {'angle': 85}
        },
        'S': {  # Retroceder
            'servo1': {'angle': 70}, 'servo2': {'angle': 110},
            'servo3': {'angle': 80}, 'servo4': {'angle': 100},
            'servo5': {'angle': 85}, 'servo6': {'angle': 95}
        },
        'A': {  # Izquierda
            'servo1': {'angle': 100}, 'servo2': {'angle': 100},
            'servo3': {'angle': 80}, 'servo4': {'angle': 80},
            'servo5': {'angle': 90}, 'servo6': {'angle': 90}
        },
        'D': {  # Derecha
            'servo1': {'angle': 80}, 'servo2': {'angle': 80},
            'servo3': {'angle': 100}, 'servo4': {'angle': 100},
            'servo5': {'angle': 90}, 'servo6': {'angle': 90}
        },
        'STOP': {  # Detener
            'servo1': {'angle': 90}, 'servo2': {'angle': 90},
            'servo3': {'angle': 90}, 'servo4': {'angle': 90},
            'servo5': {'angle': 90}, 'servo6': {'angle': 90}
        }
    }
    
    if cmd in movements:
        with state_lock:
            for servo_id, values in movements[cmd].items():
                servo_state[servo_id].update(values)
        return jsonify({'status': 'ok', 'command': cmd, 'servos': servo_state})
    
    return jsonify({'error': 'Comando no válido'}), 400

# Endpoint para obtener datos de telemetría (para gráficas)
@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    # Datos simulados para las gráficas
    telemetry = {
        'timestamp': time.time(),
        'angles': [servo_state[f'servo{i}']['angle'] for i in range(1, 7)],
        'errors': [random.uniform(-5, 5) for _ in range(6)],
        'pwm': [random.randint(1000, 2000) for _ in range(6)]
    }
    return jsonify(telemetry)

# Endpoint para verificar disponibilidad de cámara WebSocket
@app.route('/api/camera/status', methods=['GET'])
def camera_status():
    return jsonify({
        'available': camera_available,
        'url': camera_url if camera_available else None
    })

# Server-Sent Events para streaming de datos en tiempo real
@app.route('/api/stream')
def stream():
    def generate():
        while True:
            with state_lock:
                data = {
                    'servos': servo_state,
                    'timestamp': time.time()
                }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(0.1)  # 10Hz
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)