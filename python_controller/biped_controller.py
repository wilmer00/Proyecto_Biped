#!/usr/bin/env python3
import cv2
import numpy as np
import threading
import time
import json
import os
from websocket import create_connection, WebSocketConnectionClosedException

# Solución Wayland
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class BipedController:
    def __init__(self, esp32_ip):
        self.ip = esp32_ip
        self.ws = None
        self.connected = False
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        self.frame_count = 0
        self.mode = "idle"
        self.servo_angles = [90, 90, 90, 90, 90, 90]
        self.servos_enabled = True
        self.last_slider_values = [90] * 6
        
        print(f"🤖 Controlador iniciado - IP: {esp32_ip}")
        self.start_video_thread()
        self.start_websocket_thread()
        
    def start_video_thread(self):
        def video_loop():
            stream_url = f"http://{self.ip}/"
            print(f"📹 Intentando video: {stream_url}")
            
            retry_delay = 2
            while self.running:
                try:
                    cap = cv2.VideoCapture(stream_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    if not cap.isOpened():
                        print(f"❌ Stream no disponible, reintentando...")
                        time.sleep(retry_delay)
                        continue
                    
                    print("✅ Stream de video ABIERTO")
                    
                    while self.running:
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            with self.lock:
                                self.frame = cv2.resize(frame, (640, 480))
                                self.frame_count += 1
                        else:
                            time.sleep(0.05)
                    
                    cap.release()
                            
                except Exception as e:
                    print(f"Error video: {e}")
                    time.sleep(retry_delay)
        
        threading.Thread(target=video_loop, daemon=True).start()
    
    def start_websocket_thread(self):
        def ws_loop():
            print(f"📡 Intentando WebSocket: ws://{self.ip}:82")
            retry_delay = 2
            
            while self.running:
                try:
                    self.ws = create_connection(f"ws://{self.ip}:82", timeout=5)
                    self.connected = True
                    print("✅ WebSocket CONECTADO")
                    
                    # Solicitar estado inicial
                    self.send_command("get_status")
                    
                    while self.running and self.connected:
                        try:
                            message = self.ws.recv()
                            if message:
                                data = json.loads(message)
                                self.mode = data.get("mode", "idle")
                                self.servo_angles = data.get("servos", [90]*6)
                                self.servos_enabled = data.get("servos_enabled", True)
                        except WebSocketConnectionClosedException:
                            self.connected = False
                            print("❌ WebSocket cerrado por el servidor")
                            break
                        except Exception as e:
                            if "timed out" not in str(e):
                                print(f"⚠️  Error recibiendo: {e}")
                            
                except Exception as e:
                    if self.connected:
                        print(f"❌ WebSocket error: {e}")
                    self.connected = False
                    self.ws = None
                time.sleep(retry_delay)
        
        threading.Thread(target=ws_loop, daemon=True).start()
    
    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def send_command(self, cmd, params=None):
        if not self.connected or not self.ws:
            return False
        
        try:
            payload = {"cmd": cmd}
            if params:
                payload.update(params)
            self.ws.send(json.dumps(payload))
            return True
        except Exception as e:
            print(f"Error enviando: {e}")
            self.connected = False
            return False
    
    def set_all_servos(self, angles):
        """Envía posiciones de todos los servos en un solo comando"""
        return self.send_command("set_all_servos", {"angles": angles})
    
    def disable_servos(self):
        """Deshabilita torque de todos los servos"""
        return self.send_command("disable_servos")
    
    def enable_servos(self):
        """Habilita torque de todos los servos"""
        return self.send_command("enable_servos")

def create_control_panel(controller):
    """Crea un panel de control con información de estado"""
    panel = np.zeros((300, 640, 3), dtype=np.uint8)
    panel[:] = (30, 30, 30)
    
    # Título
    cv2.putText(panel, "CONTROL MANUAL DE SERVOS", (160, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Estado de conexión
    ws_color = (0, 255, 0) if controller.connected else (0, 0, 255)
    ws_text = "CONECTADO" if controller.connected else "DESCONECTADO"
    cv2.circle(panel, (30, 60), 8, ws_color, -1)
    cv2.putText(panel, f"WebSocket: {ws_text}", (50, 65), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, ws_color, 1)
    
    # Estado de servos
    servo_color = (0, 255, 0) if controller.servos_enabled else (100, 100, 100)
    servo_text = "HABILITADOS" if controller.servos_enabled else "DESHABILITADOS"
    cv2.circle(panel, (350, 60), 8, servo_color, -1)
    cv2.putText(panel, f"Servos: {servo_text}", (370, 65), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, servo_color, 1)
    
    # Nombres de servos
    servo_names = ["Cadera Izq", "Cadera Der", "Rodilla Izq", 
                   "Rodilla Der", "Pie Izq", "Pie Der"]
    
    y_start = 100
    for i, name in enumerate(servo_names):
        y = y_start + i * 30
        cv2.putText(panel, name, (20, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Mostrar ángulo actual del ESP32
        angle = controller.servo_angles[i]
        color = (0, 255, 255) if controller.servos_enabled else (100, 100, 100)
        cv2.putText(panel, f"{angle:>3}°", (450, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Barra visual del ángulo
        bar_x = 250
        bar_width = int((angle / 180.0) * 150)
        cv2.rectangle(panel, (bar_x, y-12), (bar_x + bar_width, y-4), color, -1)
        cv2.rectangle(panel, (bar_x, y-12), (bar_x + 150, y-4), (100, 100, 100), 1)
    
    # Instrucciones
    cv2.putText(panel, "Teclas: [i]IDLE [w]WALK [m]MANUAL [s]STAND [e]ENABLE [d]DISABLE [q]QUIT", 
                (10, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 1)
    
    return panel

def main():
    # ✅ ACTUALIZA ESTA IP con la que muestra el Monitor Serial
    ESP32_IP = "10.181.145.31"
    
    print("\n" + "="*60)
    print("ROBOT BIPED - CONTROLADOR MEJORADO CON SYNC")
    print("="*60)
    print(f"IP ESP32: {ESP32_IP}")
    
    # Verificar conectividad
    print("\n🔍 VERIFICANDO CONECTIVIDAD...")
    import subprocess
    try:
        result = subprocess.run(['ping', '-c', '2', '-W', '2', ESP32_IP], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ ESP32 responde al ping")
        else:
            print("❌ ESP32 NO responde")
            print("💡 Solución: Conecta tu PC al WiFi 'Redmi'")
            return
    except Exception as e:
        print(f"⚠️  No se pudo verificar ping: {e}")
    
    controller = BipedController(ESP32_IP)
    
    # Esperar conexiones
    print("\n⏳ Esperando conexiones (10s máximo)...")
    for i in range(10):
        time.sleep(1)
        if controller.connected or controller.frame is not None:
            break
        print(f"  {i+1}/10...")
    
    if not controller.connected and controller.frame is None:
        print("\n❌ NO SE PUDO CONECTAR")
        print("\n🔧 Verifica:")
        print("  1. El ESP32 está encendido")
        print("  2. Estás conectado al WiFi 'Redmi'")
        print("  3. La IP coincide con el Monitor Serial")
        return
    
    # Crear ventana OpenCV
    window_name = "Biped Camera + Control"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 640, 780)
    
    # Crear sliders para cada servo
    servo_names = ["Cadera_Izq", "Cadera_Der", "Rodilla_Izq", 
                   "Rodilla_Der", "Pie_Izq", "Pie_Der"]
    
    for i, name in enumerate(servo_names):
        cv2.createTrackbar(name, window_name, 90, 180, lambda x: None)
    
    print("\n" + "="*60)
    print("✅ SISTEMA LISTO - CONTROLES ACTIVOS")
    print("="*60)
    print("\n📋 CONTROLES DEL TECLADO:")
    print("  [i] Modo IDLE (detener)")
    print("  [w] Modo WALK (caminar automático)")
    print("  [m] Modo MANUAL (control con sliders)")
    print("  [s] STAND (posición de pie recto)")
    print("  [e] ENABLE servos (habilitar torque)")
    print("  [d] DISABLE servos (sin torque - relajados)")
    print("  [q] Salir")
    print("\n🎮 SLIDERS:")
    print("  Arrastra los sliders para mover cada servo (0-180°)")
    print("  Los valores se sincronizan automáticamente con el ESP32")
    print("="*60 + "\n")
    
    last_mode = ""
    last_servo_send = time.time()
    slider_update_needed = True
    
    while True:
        # Obtener frame de la cámara
        frame = controller.get_frame()
        
        # Crear imagen combinada (video + panel)
        combined = np.zeros((780, 640, 3), dtype=np.uint8)
        
        if frame is not None:
            combined[0:480, 0:640] = frame
        else:
            # Mensaje de "no video"
            cv2.putText(combined, "ESPERANDO VIDEO...", (150, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 2)
        
        # Panel de control
        control_panel = create_control_panel(controller)
        combined[480:780, 0:640] = control_panel
        
        # Mostrar modo actual en el video
        mode_text = f"MODO: {controller.mode.upper()}"
        mode_color = (0, 255, 0) if controller.mode != "idle" else (100, 100, 255)
        cv2.putText(combined, mode_text, (10, 460), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, mode_color, 2)
        
        # Actualizar sliders con valores del ESP32 (solo cuando no hay cambios del usuario)
        if controller.mode == "manual" and slider_update_needed:
            for i, name in enumerate(servo_names):
                current_slider = cv2.getTrackbarPos(name, window_name)
                esp_angle = controller.servo_angles[i]
                if abs(current_slider - esp_angle) > 3:  # Solo actualizar si hay diferencia
                    cv2.setTrackbarPos(name, window_name, esp_angle)
            slider_update_needed = False
        
        # Manejo de teclado
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('i'):
            if controller.mode != "idle":
                controller.send_command("set_mode", {"mode": "idle"})
                print("🛑 Modo: IDLE")
                last_mode = "idle"
                slider_update_needed = True
                
        elif key == ord('w'):
            if controller.mode != "walk":
                controller.send_command("set_mode", {"mode": "walk"})
                print("🚶 Modo: WALK - Caminando automáticamente")
                last_mode = "walk"
                
        elif key == ord('m'):
            if controller.mode != "manual":
                controller.send_command("set_mode", {"mode": "manual"})
                print("🎮 Modo: MANUAL - Control con sliders activado")
                last_mode = "manual"
                slider_update_needed = True
                
        elif key == ord('s'):
            controller.send_command("stand")
            print("📏 Posición: DE PIE (90° todos los servos)")
            time.sleep(0.5)
            slider_update_needed = True
            
        elif key == ord('e'):
            controller.enable_servos()
            print("🔓 Servos HABILITADOS (con torque)")
            
        elif key == ord('d'):
            controller.disable_servos()
            print("🔒 Servos DESHABILITADOS (sin torque - relajados)")
            
        elif key == ord('q'):
            break
        
        # Control manual: enviar posiciones de sliders
        if controller.mode == "manual" and controller.connected:
            current_time = time.time()
            if current_time - last_servo_send > 0.05:  # 20 Hz
                # Leer todos los sliders
                new_angles = []
                changed = False
                
                for i, name in enumerate(servo_names):
                    angle = cv2.getTrackbarPos(name, window_name)
                    new_angles.append(angle)
                    if abs(angle - controller.last_slider_values[i]) > 1:
                        changed = True
                
                # Enviar solo si hubo cambios
                if changed:
                    controller.set_all_servos(new_angles)
                    controller.last_slider_values = new_angles.copy()
                    last_servo_send = current_time
        
        # Mostrar frame combinado
        cv2.imshow(window_name, combined)
    
    controller.running = False
    cv2.destroyAllWindows()
    print("\n✅ Sistema detenido correctamente")
    print("👋 ¡Hasta pronto!\n")

if __name__ == "__main__":
    main()