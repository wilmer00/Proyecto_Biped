"""
Vista 3D del robot usando OpenGL
"""
import sys
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from config.settings import Config


class Robot3DView(QGLWidget):
    """Widget de visualización 3D del robot bípedo"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.servo_angles = [90] * 6
        self.joint_positions = {}
        self.rotation_x = 20
        self.rotation_y = 0
        self.zoom = -400
        self.last_pos = None
        
    def initializeGL(self):
        """Inicializar OpenGL"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Configurar luz
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        
        glClearColor(0.1, 0.1, 0.15, 1.0)
        
    def resizeGL(self, w, h):
        """Redimensionar viewport"""
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w/h if h != 0 else 1, 1, 1000)
        glMatrixMode(GL_MODELVIEW)
        
    def paintGL(self):
        """Renderizar la escena"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Cámara
        glTranslatef(0, 0, self.zoom)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Dibujar suelo
        self.draw_ground()
        
        # Dibujar robot
        self.draw_robot()
        
        # Dibujar ejes de coordenadas
        self.draw_axes()
        
    def draw_ground(self):
        """Dibujar el suelo con rejilla"""
        glColor3f(0.2, 0.2, 0.25)
        glBegin(GL_LINES)
        for i in range(-200, 201, 20):
            glVertex3f(i, -220, -200)
            glVertex3f(i, -220, 200)
            glVertex3f(-200, -220, i)
            glVertex3f(200, -220, i)
        glEnd()
        
    def draw_axes(self):
        """Dibujar ejes X, Y, Z"""
        glBegin(GL_LINES)
        # X - Rojo
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(50, 0, 0)
        # Y - Verde
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 50, 0)
        # Z - Azul
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 50)
        glEnd()
        
    def draw_robot(self):
        """Dibujar el robot completo"""
        # Cuerpo
        glPushMatrix()
        glColor3f(0.3, 0.5, 0.8)
        glTranslatef(0, 0, 0)
        self.draw_box(60, 80, 30)
        glPopMatrix()
        
        # Cabeza (cámara)
        glPushMatrix()
        glColor3f(0.2, 0.4, 0.7)
        glTranslatef(0, 50, 0)
        self.draw_sphere(20)
        # Lente de cámara
        glColor3f(0.1, 0.1, 0.1)
        glTranslatef(0, 0, 20)
        self.draw_sphere(8)
        glPopMatrix()
        
        # Piernas
        if self.joint_positions:
            self.draw_leg_from_positions(is_left=True)
            self.draw_leg_from_positions(is_left=False)
        else:
            # Piernas por defecto si no hay posiciones calculadas
            self.draw_default_legs()
            
    def draw_leg_from_positions(self, is_left):
        """Dibujar pierna usando posiciones calculadas por cinemática"""
        if is_left:
            hip_pos = self.joint_positions.get("left_hip", (-50, 0, 0))
            knee_pos = self.joint_positions.get("left_knee", (-50, 0, -100))
            foot_pos = self.joint_positions.get("left_foot", (-50, 0, -200))
            color = (0.8, 0.3, 0.3)
        else:
            hip_pos = self.joint_positions.get("right_hip", (50, 0, 0))
            knee_pos = self.joint_positions.get("right_knee", (50, 0, -100))
            foot_pos = self.joint_positions.get("right_foot", (50, 0, -200))
            color = (0.3, 0.8, 0.3)
        
        glColor3f(*color)
        
        # Articulación de cadera
        glPushMatrix()
        glTranslatef(*hip_pos)
        self.draw_sphere(12)
        glPopMatrix()
        
        # Muslo
        self.draw_cylinder(hip_pos, knee_pos, 8)
        
        # Articulación de rodilla
        glPushMatrix()
        glTranslatef(*knee_pos)
        self.draw_sphere(10)
        glPopMatrix()
        
        # Pantorrilla
        self.draw_cylinder(knee_pos, foot_pos, 7)
        
        # Pie
        glPushMatrix()
        glTranslatef(*foot_pos)
        glColor3f(0.2, 0.2, 0.2)
        self.draw_box(25, 10, 40)
        glPopMatrix()
        
    def draw_default_legs(self):
        """Dibujar piernas en posición por defecto"""
        # Pierna izquierda
        glColor3f(0.8, 0.3, 0.3)
        self.draw_cylinder((-50, 0, 0), (-50, 0, -100), 8)
        self.draw_cylinder((-50, 0, -100), (-50, 0, -200), 7)
        
        # Pierna derecha
        glColor3f(0.3, 0.8, 0.3)
        self.draw_cylinder((50, 0, 0), (50, 0, -100), 8)
        self.draw_cylinder((50, 0, -100), (50, 0, -200), 7)
        
    def draw_box(self, width, height, depth):
        """Dibujar una caja"""
        w, h, d = width/2, height/2, depth/2
        glBegin(GL_QUADS)
        # Frente
        glNormal3f(0, 0, 1)
        glVertex3f(-w, -h, d)
        glVertex3f(w, -h, d)
        glVertex3f(w, h, d)
        glVertex3f(-w, h, d)
        # Atrás
        glNormal3f(0, 0, -1)
        glVertex3f(-w, -h, -d)
        glVertex3f(-w, h, -d)
        glVertex3f(w, h, -d)
        glVertex3f(w, -h, -d)
        # Arriba
        glNormal3f(0, 1, 0)
        glVertex3f(-w, h, -d)
        glVertex3f(-w, h, d)
        glVertex3f(w, h, d)
        glVertex3f(w, h, -d)
        # Abajo
        glNormal3f(0, -1, 0)
        glVertex3f(-w, -h, -d)
        glVertex3f(w, -h, -d)
        glVertex3f(w, -h, d)
        glVertex3f(-w, -h, d)
        # Izquierda
        glNormal3f(-1, 0, 0)
        glVertex3f(-w, -h, -d)
        glVertex3f(-w, -h, d)
        glVertex3f(-w, h, d)
        glVertex3f(-w, h, -d)
        # Derecha
        glNormal3f(1, 0, 0)
        glVertex3f(w, -h, -d)
        glVertex3f(w, h, -d)
        glVertex3f(w, h, d)
        glVertex3f(w, -h, d)
        glEnd()
        
    def draw_sphere(self, radius):
        """Dibujar una esfera"""
        quadric = gluNewQuadric()
        gluSphere(quadric, radius, 16, 16)
        gluDeleteQuadric(quadric)
        
    def draw_cylinder(self, start, end, radius):
        """Dibujar cilindro entre dos puntos"""
        x1, y1, z1 = start
        x2, y2, z2 = end
        
        dx = x2 - x1
        dy = y2 - y1
        dz = z2 - z1
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if length < 0.001:
            return
        
        glPushMatrix()
        glTranslatef(x1, y1, z1)
        
        # Rotar cilindro para alinearlo
        ax = 57.2957795*math.acos(dz/length)
        if dz < 0:
            ax = -ax
        rx = -dy*dz
        ry = dx*dz
        glRotatef(ax, rx, ry, 0)
        
        quadric = gluNewQuadric()
        gluCylinder(quadric, radius, radius, length, 12, 1)
        gluDeleteQuadric(quadric)
        
        glPopMatrix()
        
    def update_servo_angles(self, angles):
        """Actualizar ángulos de servos"""
        self.servo_angles = angles
        self.update()
        
    def update_joint_positions(self, positions):
        """Actualizar posiciones de articulaciones"""
        self.joint_positions = positions
        self.update()
        
    def mousePressEvent(self, event):
        """Iniciar rotación con mouse"""
        self.last_pos = event.pos()
        
    def mouseMoveEvent(self, event):
        """Rotar vista con mouse"""
        if self.last_pos:
            dx = event.x() - self.last_pos.x()
            dy = event.y() - self.last_pos.y()
            self.rotation_y += dx * 0.5
            self.rotation_x += dy * 0.5
            self.last_pos = event.pos()
            self.update()
            
    def wheelEvent(self, event):
        """Zoom con rueda del mouse"""
        delta = event.angleDelta().y()
        self.zoom += delta * 0.5
        self.zoom = max(-800, min(-100, self.zoom))
        self.update()