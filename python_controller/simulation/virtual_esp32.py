"""
Simulador virtual del ESP32 para desarrollo sin hardware
"""
import cv2
import numpy as np
import threading
import time
import math
from config.settings import Config


class VirtualESP32:
    """Simula el comportamiento del ESP32 sin hardware real"""
    
    def __init__(self):
        self.mode = "idle"
        self.servo_angles = [Config.SERVO_DEFAULT_ANGLE] * Config.NUM_SERVOS
        self.target_angles = self.servo_angles.copy()
        self.running = False
        self.thread = None
        
        # PID para cada servo
        self.pid_errors = [0] * Config.NUM_SERVOS
        self.pid_integrals = [0] * Config.NUM_SERVOS
        self.pid_derivatives = [0] * Config.NUM_SERVOS
        
        # Parámetros PID (Kp, Ki, Kd)
        self.pid_params = [
            [Config.PID_KP_DEFAULT, Config.PID_KI_DEFAULT, Config.PID_KD_DEFAULT]
            for _ in range(Config.NUM_SERVOS)
        ]
        
        # Callbacks
        self.on_state_update = None
        
        # Generación de video simulado
        self.virtual_camera = VirtualCamera()
        
    def start(self):
        """Iniciar simulación"""
        if self.running:
            return
            
        self.running = True
        self.virtual_camera.start()
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()
        print("🤖 Simulación ESP32 iniciada")
        
    def stop(self):
        """Detener simulación"""
        self.running = False
        self.virtual_camera.stop()
        if self.thread:
            self.thread.join(timeout=2)
        print("🤖 Simulación ESP32 detenida")
        
    def _simulation_loop(self):
        """Loop principal de simulación"""
        dt = 0.02  # 50 Hz
        
        while self.running:
            start_time = time.time()
            
            # Simular movimiento de servos con PID
            for i in range(Config.NUM_SERVOS):
                self._update_servo_pid(i, dt)
            
            # Simular caminata automática
            if self.mode == "walk":
                self._simulate_walk()
            
            # Notificar cambios
            if self.on_state_update:
                self.on_state_update({
                    "mode": self.mode,
                    "servos": self.servo_angles.copy(),
                    "targets": self.target_angles.copy(),
                    "pid_errors": self.pid_errors.copy()
                })
            
            # Mantener frecuencia
            elapsed = time.time() - start_time
            if elapsed < dt:
                time.sleep(dt - elapsed)
                
    def _update_servo_pid(self, servo_id, dt):
        """Actualizar posición de servo con control PID"""
        target = self.target_angles[servo_id]
        current = self.servo_angles[servo_id]
        
        # Calcular error
        error = target - current
        
        # PID
        kp, ki, kd = self.pid_params[servo_id]
        
        self.pid_integrals[servo_id] += error * dt
        derivative = (error - self.pid_errors[servo_id]) / dt if dt > 0 else 0
        
        output = kp * error + ki * self.pid_integrals[servo_id] + kd * derivative
        
        # Aplicar límites de velocidad (simular inercia)
        max_change = 5.0  # grados por ciclo
        output = max(-max_change, min(max_change, output))
        
        # Actualizar posición
        new_angle = current + output
        new_angle = max(Config.SERVO_MIN_ANGLE, min(Config.SERVO_MAX_ANGLE, new_angle))
        
        self.servo_angles[servo_id] = new_angle
        self.pid_errors[servo_id] = error
        
    def _simulate_walk(self):
        """Simular patrón de caminata"""
        t = time.time() * Config.WALK_SPEED
        
        # Patrón sinusoidal para caderas
        self.target_angles[Config.SERVO_MAP["left_hip"]] = 90 + 20 * math.sin(t)
        self.target_angles[Config.SERVO_MAP["right_hip"]] = 90 - 20 * math.sin(t)
        
        # Rodillas con fase desplazada
        self.target_angles[Config.SERVO_MAP["left_knee"]] = 90 + 15 * math.sin(t + math.pi/4)
        self.target_angles[Config.SERVO_MAP["right_knee"]] = 90 - 15 * math.sin(t + math.pi/4)
        
        # Pies
        self.target_angles[Config.SERVO_MAP["left_ankle"]] = 90 + 10 * math.sin(t + math.pi/2)
        self.target_angles[Config.SERVO_MAP["right_ankle"]] = 90 - 10 * math.sin(t + math.pi/2)
        
    def set_mode(self, mode):
        """Cambiar modo de operación"""
        if mode in Config.MODES:
            self.mode = mode
            print(f"Modo cambiado a: {mode}")
            return True
        return False
        
    def set_servo(self, servo_id, angle):
        """Establecer ángulo objetivo de un servo"""
        if 0 <= servo_id < Config.NUM_SERVOS:
            angle = max(Config.SERVO_MIN_ANGLE, min(Config.SERVO_MAX_ANGLE, angle))
            self.target_angles[servo_id] = angle
            return True
        return False
        
    def set_all_servos(self, angles):
        """Establecer todos los servos"""
        if len(angles) == Config.NUM_SERVOS:
            self.target_angles = [
                max(Config.SERVO_MIN_ANGLE, min(Config.SERVO_MAX_ANGLE, a))
                for a in angles
            ]
            return True
        return False
        
    def set_pid_params(self, servo_id, kp, ki, kd):
        """Configurar parámetros PID de un servo"""
        if 0 <= servo_id < Config.NUM_SERVOS:
            self.pid_params[servo_id] = [kp, ki, kd]
            return True
        return False
        
    def get_state(self):
        """Obtener estado actual"""
        return {
            "mode": self.mode,
            "servo_angles": self.servo_angles.copy(),
            "target_angles": self.target_angles.copy(),
            "pid_errors": self.pid_errors.copy(),
            "pid_params": [p.copy() for p in self.pid_params]
        }
        
    def get_frame(self):
        """Obtener frame de la cámara virtual"""
        return self.virtual_camera.get_frame()


class VirtualCamera:
  """Genera video sintético para simulación"""
  
  def __init__(self):
    self.running = False
    self.frame = None
    self.thread = None
      
  def start(self):
    self.running = True
    self.thread = threading.Thread(target=self._generate_frames, daemon=True)
    self.thread.start()
      
  def stop(self):
    self.running = False
    if self.thread:
        self.thread.join(timeout=1)
          
  def _generate_frames(self):
    """Generar frames sintéticos"""
    while self.running:
        # Crear imagen base
        frame = np.zeros((Config.CAMERA_HEIGHT, Config.CAMERA_WIDTH, 3), dtype=np.uint8)
        
        # Fondo gradiente
        for y in range(Config.CAMERA_HEIGHT):
            color = int(50 + (y / Config.CAMERA_HEIGHT) * 100)
            frame[y, :] = [color, color // 2, color // 3]
        
        # Agregar elementos visuales
        t = time.time()
        
        # "Minerales" simulados (círculos que se mueven)
        mineral_x = int(200 + 100 * math.sin(t * 0.5))
        mineral_y = int(240 + 80 * math.cos(t * 0.3))
        cv2.circle(frame, (mineral_x, mineral_y), 30, (0, 255, 255), -1)
        cv2.putText(frame, "MINERAL", (mineral_x - 40, mineral_y - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Información de simulación
        cv2.putText(frame, "MODO SIMULACION", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"FPS: {int(1/0.033)}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        self.frame = frame
        time.sleep(0.033)  # ~30 FPS
          
  def get_frame(self):
    return self.frame.copy() if self.frame is not None else None