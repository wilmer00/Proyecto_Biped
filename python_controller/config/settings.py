"""
Configuración global del sistema
"""

class Config:
    SIMULATION_MODE = True  # False para usar ESP32 real
    
    # ESP32 Connection
    ESP32_IP = "10.181.145.31"
    WEBSOCKET_PORT = 82
    STREAM_URL_TEMPLATE = "http://{ip}/"
    
    # Servos (6 servos para las piernas)
    NUM_SERVOS = 6
    SERVO_NAMES = [
        "Cadera Izquierda",
        "Cadera Derecha", 
        "Rodilla Izquierda",
        "Rodilla Derecha",
        "Pie Izquierdo",
        "Pie Derecho"
    ]
    SERVO_MIN_ANGLE = 0
    SERVO_MAX_ANGLE = 180
    SERVO_DEFAULT_ANGLE = 90
    
    # Mapeo de servos a partes del robot
    SERVO_MAP = {
        "left_hip": 0,
        "right_hip": 1,
        "left_knee": 2,
        "right_knee": 3,
        "left_ankle": 4,
        "right_ankle": 5
    }
    
    # PID Parameters
    PID_KP_DEFAULT = 2.6
    PID_KI_DEFAULT = 1.05
    PID_KD_DEFAULT = 0.75
    
    # Camera
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    
    # AI Model
    MODEL_PATH = "models/mineral_detector.h5"
    DATASET_PATH = "datasets/"
    IMAGE_SIZE = (224, 224)
    CONFIDENCE_THRESHOLD = 0.7
    
    # UI
    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 900
    UPDATE_INTERVAL = 30  # ms
    
    # 3D Visualization
    LEG_LENGTH_1 = 100  # Longitud muslo (mm)
    LEG_LENGTH_2 = 100  # Longitud pantorrilla (mm)
    FOOT_SIZE = 30      # Tamaño del pie (mm)
    
    # Gait patterns
    STEP_HEIGHT = 30    # mm
    STEP_LENGTH = 50    # mm
    WALK_SPEED = 1.0    # velocidad relativa
    
    # Modes
    MODES = ["idle", "walk", "manual", "scan"]