#!/usr/bin/env python3
"""
Sistema de Control de Robot Bípedo
Incluye: Control de hardware, Simulación, IA, Visualización 3D
"""
import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QMessageBox, QProgressDialog
from PyQt5.QtCore import Qt

# Importar módulos del proyecto
from config.settings import Config
from hardware.esp32_camera import ESP32Camera
from hardware.esp32_websocket import ESP32WebSocket
from simulation.virtual_esp32 import VirtualESP32
from kinematics.leg_controller import LegController
from ai.mineral_detector import MineralDetector
from ui.main_window import MainWindow


class RobotController:
    """Controlador principal que unifica hardware y simulación"""
    
    def __init__(self, simulation_mode=True):
        self.simulation_mode = simulation_mode
        
        if simulation_mode:
            print("🤖 Iniciando en MODO SIMULACIÓN")
            self.virtual_esp32 = VirtualESP32()
            self.camera = None
            self.websocket = None
        else:
            print("🔌 Iniciando en MODO HARDWARE REAL")
            self.virtual_esp32 = None
            self.camera = ESP32Camera()
            self.websocket = ESP32WebSocket()
            
    def start(self):
        """Iniciar todos los componentes"""
        if self.simulation_mode:
            self.virtual_esp32.start()
        else:
            self.camera.start()
            self.websocket.start()
            
            # Esperar conexión
            print("Esperando conexión con ESP32...")
            for _ in range(10):
                time.sleep(0.5)
                if self.camera.is_connected() or self.websocket.is_connected():
                    break
                    
    def stop(self):
        """Detener todos los componentes"""
        if self.simulation_mode:
            if self.virtual_esp32:
                self.virtual_esp32.stop()
        else:
            if self.camera:
                self.camera.stop()
            if self.websocket:
                self.websocket.stop()
                
    def get_frame(self):
        """Obtener frame de la cámara"""
        if self.simulation_mode:
            return self.virtual_esp32.get_frame()
        else:
            return self.camera.get_frame() if self.camera else None
            
    def set_mode(self, mode):
        """Cambiar modo de operación"""
        if self.simulation_mode:
            return self.virtual_esp32.set_mode(mode)
        else:
            return self.websocket.set_mode(mode) if self.websocket else False
            
    def set_servo(self, servo_id, angle):
        """Mover un servo"""
        if self.simulation_mode:
            return self.virtual_esp32.set_servo(servo_id, angle)
        else:
            return self.websocket.set_servo(servo_id, angle) if self.websocket else False
            
    def set_all_servos(self, angles):
        """Mover todos los servos"""
        if self.simulation_mode:
            return self.virtual_esp32.set_all_servos(angles)
        else:
            return self.websocket.set_all_servos(angles) if self.websocket else False
            
    def get_state(self):
        """Obtener estado actual"""
        if self.simulation_mode:
            state = self.virtual_esp32.get_state()
            state['connected'] = True
            return state
        else:
            if self.websocket:
                return self.websocket.get_state()
            return {
                'connected': False,
                'mode': 'idle',
                'servo_angles': [90] * 6,
                'sensor_data': {}
            }
            
    def get_mode(self):
        """Obtener modo actual"""
        state = self.get_state()
        return state.get('mode', 'idle')


def check_dependencies():
    """Verificar que todas las dependencias estén instaladas"""
    missing = []
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
        
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
        
    try:
        from PyQt5 import QtWidgets
    except ImportError:
        missing.append("PyQt5")
        
    try:
        from OpenGL import GL
    except ImportError:
        missing.append("pyopengl")
        
    try:
        import tensorflow
    except ImportError:
        missing.append("tensorflow")
        
    try:
        import websocket
    except ImportError:
        missing.append("websocket-client")
        
    if missing:
        print("❌ Dependencias faltantes:")
        for dep in missing:
            print(f"   - {dep}")
        print("\nInstala con: pip install " + " ".join(missing))
        return False
        
    print("✅ Todas las dependencias instaladas")
    return True


def setup_directories():
    """Crear directorios necesarios"""
    directories = ['models', 'datasets', 'logs']
    for d in directories:
        os.makedirs(d, exist_ok=True)
        
    # Verificar dataset
    if not os.path.exists(Config.DATASET_PATH):
        print(f"⚠️ Carpeta de dataset no encontrada: {Config.DATASET_PATH}")
        print("   Crea carpetas en 'datasets/' con imágenes de minerales")
    else:
        subdirs = [d for d in os.listdir(Config.DATASET_PATH) 
                   if os.path.isdir(os.path.join(Config.DATASET_PATH, d))]
        if subdirs:
            print(f"✅ Dataset encontrado: {len(subdirs)} clases")
        else:
            print("⚠️ Dataset vacío")


def main():
    """Función principal"""
    print("="*60)
    print("ROBOT BÍPEDO - SISTEMA DE CONTROL COMPLETO")
    print("="*60)
    print()
    
    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)
        
    # Crear directorios
    setup_directories()
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Splash screen de carga
    splash_msg = QProgressDialog("Iniciando sistema...", None, 0, 4)
    splash_msg.setWindowTitle("Cargando")
    splash_msg.setWindowModality(Qt.WindowModal)
    splash_msg.show()
    app.processEvents()
    
    try:
        # Paso 1: Inicializar controlador
        splash_msg.setValue(1)
        splash_msg.setLabelText("Inicializando controlador...")
        app.processEvents()
        
        controller = RobotController(simulation_mode=Config.SIMULATION_MODE)
        controller.start()
        time.sleep(0.5)
        
        # Paso 2: Inicializar cinemática
        splash_msg.setValue(2)
        splash_msg.setLabelText("Configurando cinemática...")
        app.processEvents()
        
        leg_controller = LegController()
        time.sleep(0.3)
        
        # Paso 3: Cargar modelo de IA
        splash_msg.setValue(3)
        splash_msg.setLabelText("Cargando detector de minerales...")
        app.processEvents()
        
        mineral_detector = MineralDetector()
        
        # Intentar cargar modelo existente
        if os.path.exists(Config.MODEL_PATH):
            mineral_detector.load_model()
        else:
            print("⚠️ Modelo no encontrado. Entrena con: python -m ai.model_trainer")
        
        time.sleep(0.3)
        
        # Paso 4: Crear interfaz
        splash_msg.setValue(4)
        splash_msg.setLabelText("Creando interfaz gráfica...")
        app.processEvents()
        
        window = MainWindow(controller, leg_controller, mineral_detector)
        window.show()
        
        splash_msg.close()
        
        print()
        print("="*60)
        print("✅ SISTEMA LISTO")
        print("="*60)
        print(f"Modo: {'SIMULACIÓN' if Config.SIMULATION_MODE else 'HARDWARE REAL'}")
        print(f"Servos: {Config.NUM_SERVOS}")
        print(f"Modelo IA: {'Cargado' if mineral_detector.is_trained else 'No disponible'}")
        print()
        print("Controles:")
        print("  - Usa los botones para cambiar modo")
        print("  - Arrastra sliders para controlar servos (modo MANUAL)")
        print("  - Click derecho en vista 3D para rotar")
        print("  - Rueda del mouse para zoom")
        print("="*60)
        
        # Ejecutar aplicación
        sys.exit(app.exec_())
        
    except Exception as e:
        splash_msg.close()
        QMessageBox.critical(None, "Error", f"Error al iniciar: {str(e)}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        # Limpiar
        try:
            controller.stop()
        except:
            pass


if __name__ == "__main__":
    main()