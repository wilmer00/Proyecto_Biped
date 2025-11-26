"""
Controlador de cinemática inversa para las piernas del robot
"""
import math
import numpy as np
from config.settings import Config


class LegController:
    """Control cinemático de las piernas del robot bípedo"""
    
    def __init__(self):
        self.l1 = Config.LEG_LENGTH_1  # Longitud muslo
        self.l2 = Config.LEG_LENGTH_2  # Longitud pantorrilla
        
    def inverse_kinematics_2d(self, x, y, is_left=True):
        """
        Cinemática inversa para una pierna (2D)
        
        Args:
            x, y: Posición objetivo del pie
            is_left: True si es pierna izquierda
            
        Returns:
            (hip_angle, knee_angle, ankle_angle) en grados
        """
        # Distancia al objetivo
        distance = math.sqrt(x**2 + y**2)
        
        # Verificar si es alcanzable
        if distance > (self.l1 + self.l2) or distance < abs(self.l1 - self.l2):
            print(f"⚠️ Posición inalcanzable: ({x}, {y})")
            return None
        
        # Ángulo de la cadera (respecto a vertical)
        hip_angle_base = math.atan2(x, -y)
        
        # Ley de cosenos para encontrar ángulo de rodilla
        cos_knee = (distance**2 - self.l1**2 - self.l2**2) / (2 * self.l1 * self.l2)
        cos_knee = max(-1, min(1, cos_knee))  # Clamp
        knee_angle = math.acos(cos_knee)
        
        # Ángulo adicional para la cadera
        cos_hip_extra = (self.l1**2 + distance**2 - self.l2**2) / (2 * self.l1 * distance)
        cos_hip_extra = max(-1, min(1, cos_hip_extra))
        hip_angle_extra = math.acos(cos_hip_extra)
        
        # Ángulo total de cadera
        hip_angle = hip_angle_base + hip_angle_extra
        
        # Ángulo del tobillo (para mantener pie horizontal)
        ankle_angle = -(hip_angle + (math.pi - knee_angle))
        
        # Convertir a grados y mapear a rango de servos (0-180)
        hip_deg = 90 - math.degrees(hip_angle)
        knee_deg = 90 + math.degrees(knee_angle - math.pi)
        ankle_deg = 90 - math.degrees(ankle_angle)
        
        # Invertir para pierna derecha
        if not is_left:
            hip_deg = 180 - hip_deg
        
        return (hip_deg, knee_deg, ankle_deg)
    
    def forward_kinematics(self, hip_angle, knee_angle, ankle_angle=90):
        """
        Cinemática directa: calcular posición del pie dados los ángulos
        
        Args:
            hip_angle, knee_angle, ankle_angle: ángulos en grados
            
        Returns:
            (x, y, z): posición del pie
        """
        # Convertir a radianes y ajustar al sistema de coordenadas
        hip_rad = math.radians(90 - hip_angle)
        knee_rad = math.radians(knee_angle - 90) + math.pi
        
        # Posición de la rodilla
        knee_x = self.l1 * math.sin(hip_rad)
        knee_y = -self.l1 * math.cos(hip_rad)
        
        # Posición del pie
        foot_x = knee_x + self.l2 * math.sin(hip_rad + knee_rad - math.pi)
        foot_y = knee_y - self.l2 * math.cos(hip_rad + knee_rad - math.pi)
        
        return (foot_x, foot_y, 0)
    
    def set_leg_position(self, x, y, z, is_left=True):
        """
        Establecer posición objetivo para una pierna completa
        
        Returns:
            [hip_angle, knee_angle, ankle_angle]
        """
        angles = self.inverse_kinematics_2d(x, y, is_left)
        if angles:
            return list(angles)
        return [90, 90, 90]  # Posición neutral si falla
    
    def get_standing_pose(self):
        """
        Obtener pose de pie (posición neutral)
        
        Returns:
            [6 ángulos]: left_hip, right_hip, left_knee, right_knee, left_ankle, right_ankle
        """
        # Piernas extendidas, pies en el suelo
        leg_height = -(self.l1 + self.l2 - 20)  # Ligeramente flexionadas
        
        left_angles = self.inverse_kinematics_2d(0, leg_height, is_left=True)
        right_angles = self.inverse_kinematics_2d(0, leg_height, is_left=False)
        
        if left_angles and right_angles:
            return [
                left_angles[0],   # cadera izq
                right_angles[0],  # cadera der
                left_angles[1],   # rodilla izq
                right_angles[1],  # rodilla der
                left_angles[2],   # tobillo izq
                right_angles[2]   # tobillo der
            ]
        
        return [90, 90, 90, 90, 90, 90]
    
    def calculate_joint_positions(self, servo_angles):
        """
        Calcular posiciones 3D de todas las articulaciones
        
        Args:
            servo_angles: lista de 6 ángulos [L_hip, R_hip, L_knee, R_knee, L_ankle, R_ankle]
            
        Returns:
            dict con posiciones de cada articulación para visualización 3D
        """
        positions = {
            "body": (0, 0, 0),
            "left_hip": (-50, 0, 0),
            "right_hip": (50, 0, 0),
            "left_knee": None,
            "right_knee": None,
            "left_foot": None,
            "right_foot": None
        }
        
        # Pierna izquierda
        left_hip_angle = servo_angles[0]
        left_knee_angle = servo_angles[2]
        left_ankle_angle = servo_angles[4]
        
        # Convertir a radianes
        hip_rad_l = math.radians(90 - left_hip_angle)
        knee_rad_l = math.radians(left_knee_angle - 90) + math.pi
        
        # Posición rodilla izquierda
        knee_x_l = -50 + self.l1 * math.sin(hip_rad_l)
        knee_y_l = -self.l1 * math.cos(hip_rad_l)
        positions["left_knee"] = (knee_x_l, 0, knee_y_l)
        
        # Posición pie izquierdo
        foot_x_l = knee_x_l + self.l2 * math.sin(hip_rad_l + knee_rad_l - math.pi)
        foot_y_l = knee_y_l - self.l2 * math.cos(hip_rad_l + knee_rad_l - math.pi)
        positions["left_foot"] = (foot_x_l, 0, foot_y_l)
        
        # Pierna derecha
        right_hip_angle = servo_angles[1]
        right_knee_angle = servo_angles[3]
        right_ankle_angle = servo_angles[5]
        
        hip_rad_r = math.radians(90 - (180 - right_hip_angle))
        knee_rad_r = math.radians(right_knee_angle - 90) + math.pi
        
        # Posición rodilla derecha
        knee_x_r = 50 + self.l1 * math.sin(hip_rad_r)
        knee_y_r = -self.l1 * math.cos(hip_rad_r)
        positions["right_knee"] = (knee_x_r, 0, knee_y_r)
        
        # Posición pie derecho
        foot_x_r = knee_x_r + self.l2 * math.sin(hip_rad_r + knee_rad_r - math.pi)
        foot_y_r = knee_y_r - self.l2 * math.cos(hip_rad_r + knee_rad_r - math.pi)
        positions["right_foot"] = (foot_x_r, 0, foot_y_r)
        
        return positions