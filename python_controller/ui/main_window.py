"""
Ventana principal de la interfaz
"""
import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from config.settings import Config
from ui.robot_3d_view import Robot3DView


class MainWindow(QMainWindow):
    """Ventana principal del sistema"""
    
    def __init__(self, controller, leg_controller, mineral_detector):
        super().__init__()
        self.controller = controller
        self.leg_controller = leg_controller
        self.mineral_detector = mineral_detector
        
        self.setWindowTitle("Robot Bípedo - Control y Simulación")
        self.setGeometry(100, 100, Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
        
        self.setup_ui()
        self.setup_timers()
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Título
        title = QLabel("🤖 ROBOT BÍPEDO - SISTEMA DE CONTROL")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2ecc71; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Layout horizontal principal
        content_layout = QHBoxLayout()
        
        # Panel izquierdo (Cámara + Controles)
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 2)
        
        # Panel derecho (Vista 3D + PID)
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 3)
        
        main_layout.addLayout(content_layout)
        
        # Barra de estado
        self.statusBar().showMessage("Sistema iniciado")
        
    def create_left_panel(self):
        """Panel izquierdo con cámara y controles"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Vista de cámara
        camera_group = QGroupBox("📹 Vista de Cámara ESP32")
        camera_layout = QVBoxLayout()
        
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("background-color: black; border: 2px solid #3498db;")
        self.camera_label.setAlignment(Qt.AlignCenter)
        camera_layout.addWidget(self.camera_label)
        
        # Info de detección
        self.detection_label = QLabel("🔍 Esperando detección...")
        self.detection_label.setStyleSheet("font-size: 14px; padding: 5px;")
        camera_layout.addWidget(self.detection_label)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Controles de modo
        mode_group = self.create_mode_controls()
        layout.addWidget(mode_group)
        
        return panel
        
    def create_right_panel(self):
        """Panel derecho con simulación 3D y PID"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Vista 3D
        view_3d_group = QGroupBox("🎮 Simulación 3D del Robot")
        view_3d_layout = QVBoxLayout()
        
        self.robot_3d = Robot3DView()
        self.robot_3d.setMinimumSize(600, 400)
        view_3d_layout.addWidget(self.robot_3d)
        
        view_3d_group.setLayout(view_3d_layout)
        layout.addWidget(view_3d_group, 3)
        
        # Panel de servos con PID
        servo_group = self.create_servo_panel()
        layout.addWidget(servo_group, 2)
        
        return panel
        
    def create_mode_controls(self):
        """Controles de modo de operación"""
        group = QGroupBox("⚙️ Modo de Operación")
        layout = QVBoxLayout()
        
        # Botones de modo
        buttons_layout = QHBoxLayout()
        
        self.btn_idle = QPushButton("🛑 IDLE")
        self.btn_idle.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold; padding: 10px;")
        self.btn_idle.clicked.connect(lambda: self.set_mode("idle"))
        
        self.btn_walk = QPushButton("🚶 WALK")
        self.btn_walk.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 10px;")
        self.btn_walk.clicked.connect(lambda: self.set_mode("walk"))
        
        self.btn_manual = QPushButton("🎮 MANUAL")
        self.btn_manual.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; padding: 10px;")
        self.btn_manual.clicked.connect(lambda: self.set_mode("manual"))
        
        self.btn_scan = QPushButton("🔍 SCAN")
        self.btn_scan.setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; padding: 10px;")
        self.btn_scan.clicked.connect(lambda: self.set_mode("scan"))
        
        buttons_layout.addWidget(self.btn_idle)
        buttons_layout.addWidget(self.btn_walk)
        buttons_layout.addWidget(self.btn_manual)
        buttons_layout.addWidget(self.btn_scan)
        
        layout.addLayout(buttons_layout)
        
        # Estado de conexión
        self.connection_label = QLabel("⚪ Desconectado")
        self.connection_label.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(self.connection_label)
        
        # Toggle simulación/real
        self.sim_checkbox = QCheckBox("Modo Simulación")
        self.sim_checkbox.setChecked(Config.SIMULATION_MODE)
        self.sim_checkbox.stateChanged.connect(self.toggle_simulation_mode)
        layout.addWidget(self.sim_checkbox)
        
        group.setLayout(layout)
        return group
        
    def create_servo_panel(self):
        """Panel de control de servos con parámetros PID"""
        group = QGroupBox("🎛️ Control de Servos y PID")
        layout = QVBoxLayout()
        
        # Tabla de servos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        servo_widget = QWidget()
        servo_layout = QVBoxLayout(servo_widget)
        
        self.servo_sliders = []
        self.servo_labels = []
        self.pid_controls = []
        
        for i in range(Config.NUM_SERVOS):
            servo_frame = self.create_servo_control(i)
            servo_layout.addWidget(servo_frame)
            
        scroll.setWidget(servo_widget)
        layout.addWidget(scroll)
        
        group.setLayout(layout)
        return group
        
    def create_servo_control(self, servo_id):
        """Crear control para un servo individual"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        layout = QGridLayout(frame)
        
        # Nombre del servo
        name_label = QLabel(Config.SERVO_NAMES[servo_id])
        name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(name_label, 0, 0, 1, 2)
        
        # Slider de ángulo
        angle_label = QLabel("Ángulo: 90°")
        layout.addWidget(angle_label, 1, 0)
        
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(Config.SERVO_MIN_ANGLE)
        slider.setMaximum(Config.SERVO_MAX_ANGLE)
        slider.setValue(Config.SERVO_DEFAULT_ANGLE)
        slider.valueChanged.connect(lambda v, lbl=angle_label, sid=servo_id: 
                                     self.on_servo_changed(sid, v, lbl))
        layout.addWidget(slider, 1, 1)
        
        self.servo_sliders.append(slider)
        self.servo_labels.append(angle_label)
        
        # Controles PID
        pid_layout = QHBoxLayout()
        
        kp_spin = QDoubleSpinBox()
        kp_spin.setPrefix("Kp: ")
        kp_spin.setRange(0, 10)
        kp_spin.setValue(Config.PID_KP_DEFAULT)
        kp_spin.setSingleStep(0.1)
        
        ki_spin = QDoubleSpinBox()
        ki_spin.setPrefix("Ki: ")
        ki_spin.setRange(0, 10)
        ki_spin.setValue(Config.PID_KI_DEFAULT)
        ki_spin.setSingleStep(0.05)
        
        kd_spin = QDoubleSpinBox()
        kd_spin.setPrefix("Kd: ")
        kd_spin.setRange(0, 10)
        kd_spin.setValue(Config.PID_KD_DEFAULT)
        kd_spin.setSingleStep(0.05)
        
        pid_layout.addWidget(kp_spin)
        pid_layout.addWidget(ki_spin)
        pid_layout.addWidget(kd_spin)
        
        layout.addLayout(pid_layout, 2, 0, 1, 2)
        
        self.pid_controls.append((kp_spin, ki_spin, kd_spin))
        
        return frame
        
    def setup_timers(self):
        """Configurar timers de actualización"""
        # Timer para actualizar video
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video)
        self.video_timer.start(Config.UPDATE_INTERVAL)
        
        # Timer para actualizar estado
        self.state_timer = QTimer()
        self.state_timer.timeout.connect(self.update_state)
        self.state_timer.start(100)
        
    def update_video(self):
        """Actualizar frame de video"""
        frame = self.controller.get_frame()
        
        if frame is not None:
            # Aplicar detección de minerales en modo SCAN
            if self.controller.get_mode() == "scan":
                detection = self.mineral_detector.predict(frame)
                frame = self.mineral_detector.draw_detection(frame, detection)
                
                if detection['detected']:
                    self.detection_label.setText(
                        f"✅ {detection['class']} detectado ({detection['confidence']:.1%})"
                    )
                    self.detection_label.setStyleSheet(
                        "font-size: 14px; padding: 5px; color: #2ecc71; font-weight: bold;"
                    )
                else:
                    self.detection_label.setText("🔍 Buscando minerales...")
                    self.detection_label.setStyleSheet("font-size: 14px; padding: 5px;")
            
            # Convertir a QImage
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Mostrar en label
            pixmap = QPixmap.fromImage(qt_image)
            self.camera_label.setPixmap(pixmap.scaled(
                self.camera_label.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
        else:
            self.camera_label.setText("❌ Sin video")
            
    def update_state(self):
        """Actualizar estado del sistema"""
        state = self.controller.get_state()
        
        # Actualizar conexión
        if state['connected']:
            self.connection_label.setText("🟢 Conectado")
            self.connection_label.setStyleSheet(
                "font-size: 14px; padding: 5px; color: #2ecc71; font-weight: bold;"
            )
        else:
            self.connection_label.setText("🔴 Desconectado")
            self.connection_label.setStyleSheet(
                "font-size: 14px; padding: 5px; color: #e74c3c; font-weight: bold;"
            )
        
        # Actualizar sliders con valores recibidos
        servo_angles = state.get('servo_angles', [90] * 6)
        for i, angle in enumerate(servo_angles):
            if i < len(self.servo_sliders):
                self.servo_sliders[i].blockSignals(True)
                self.servo_sliders[i].setValue(int(angle))
                self.servo_labels[i].setText(f"Ángulo: {int(angle)}°")
                self.servo_sliders[i].blockSignals(False)
        
        # Actualizar vista 3D
        self.robot_3d.update_servo_angles(servo_angles)
        joint_positions = self.leg_controller.calculate_joint_positions(servo_angles)
        self.robot_3d.update_joint_positions(joint_positions)
        
    def on_servo_changed(self, servo_id, value, label):
        """Handler cuando cambia un slider de servo"""
        label.setText(f"Ángulo: {value}°")
        
        # Enviar comando solo en modo manual
        if self.controller.get_mode() == "manual":
            self.controller.set_servo(servo_id, value)
            
    def set_mode(self, mode):
        """Cambiar modo de operación"""
        success = self.controller.set_mode(mode)
        if success:
            self.statusBar().showMessage(f"Modo cambiado a: {mode.upper()}")
            
    def toggle_simulation_mode(self, state):
        """Alternar entre simulación y hardware real"""
        Config.SIMULATION_MODE = (state == Qt.Checked)
        msg = "Modo SIMULACIÓN activado" if Config.SIMULATION_MODE else "Modo REAL activado"
        self.statusBar().showMessage(msg)
        QMessageBox.information(self, "Cambio de Modo", 
                                msg + "\nReinicie la aplicación para aplicar cambios.")
        
    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        reply = QMessageBox.question(self, 'Salir', 
                                    '¿Está seguro de que desea salir?',
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.controller.stop()
            event.accept()
        else:
            event.ignore()