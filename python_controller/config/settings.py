# config/settings.py
class Config:
    """Clase de configuración centralizada"""
    ESP32_IP = "192.168.1.100"
    ESP32_PORT = 80
    WEBSOCKET_PORT = 8080
    
    # Mapeo de servos
    SERVO_MAP = {
        "left_hip": 0,
        "left_knee": 1,
        "left_ankle": 2,
        "right_hip": 3,
        "right_knee": 4,
        "right_ankle": 5
    }
    
    # Límites de ángulos
    SERVO_LIMITS = {
        0: (-45, 45),
        1: (-60, 60),
        2: (-30, 30),
        3: (-45, 45),
        4: (-60, 60),
        5: (-30, 30)
    }