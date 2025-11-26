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
        self.servo_angles = [90, 90, 90, 90, 90, 90]  # 6 servos
        
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
                    self.ws = create_connection(f"ws://{self.ip}:82", timeout=3)
                    self.connected = True
                    print("✅ WebSocket CONECTADO")
                    
                    while self.running and self.connected:
                        try:
                            message = self.ws.recv(timeout=0.5)
                            if message:
                                data = json.loads(message)
                                self.mode = data.get("mode", "idle")
                                self.servo_angles = data.get("servos", [90]*6)
                        except WebSocketConnectionClosedException:
                            self.connected = False
                            break
                        except Exception:
                            pass  # Timeout normal
                            
                except Exception as e:
                    if self.connected:
                        print(f"❌ WebSocket error: {e}")
                    self.connected = False
                time.sleep(retry_delay)
        
        threading.Thread(target=ws_loop, daemon=True).start()
    
    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None
    
    def send_command(self, cmd, params=None):
        if not self.connected or not self.ws:
            print("WebSocket no conectado")
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

def create_control_panel():
    """Crea un panel de control con sliders"""
    panel = np.zeros((300, 640, 3), dtype=np.uint8)
    panel[:] = (30, 30, 30)  # Fondo gris oscuro
    
    # Títulos
    cv2.putText(panel, "CONTROL MANUAL DE SERVOS", (160, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Nombres de servos
    servo_names = ["Cadera Izq", "Cadera Der", "Rodilla Izq", 
                   "Rodilla Der", "Pie Izq", "Pie Der"]
    
    # Instrucciones
    cv2.putText(panel, "Teclas: [i] IDLE  [w] WALK  [m] MANUAL  [q] SALIR", (10, 280), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    
    return panel

def main():
    # ✅ ACTUALIZA ESTA IP con la que muestra el Monitor Serial
    ESP32_IP = "10.181.145.31"  
    
    print("\n" + "="*50)
    print("ROBOT BIPED - CONTROLADOR COMPLETO")
    print("="*50)
    print(f"IP ESP32: {ESP32_IP}")
    
    # Verificar conectividad
    print("\n🔍 VERIFICANDO CONECTIVIDAD...")
    import subprocess
    try:
        result = subprocess.run(['ping', '-c', '2', ESP32_IP], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ ESP32 responde al ping")
        else:
            print("❌ ESP32 NO responde")
            print("Solución: Conecta tu PC al WiFi 'Redmi' del móvil")
            return
    except:
        print("⚠️ No se pudo verificar ping")
    
    controller = BipedController(ESP32_IP)
    
    # ✅ Esperar conexiones con máximo 5 intentos
    print("\nEsperando conexiones (10s máximo)...")
    for i in range(5):
        time.sleep(2)
        if controller.connected or controller.frame is not None:
            break
        print(f"Intento {i+1}/5...")
    
    if not controller.connected and controller.frame is None:
        print("\n❌ NO SE PUDO CONECTAR")
        print("Verifica:")
        print("1. El ESP32 está encendido")
        print("2. Estás conectado al WiFi 'Redmi'")
        print("3. La IP es correcta")
        return
    
    # Crear ventanas de OpenCV
    cv2.namedWindow("Biped Camera + Control", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Biped Camera + Control", 640, 780)
    
    # Crear panel de control
    control_panel = create_control_panel()
    
    # Sliders para cada servo (0-180 grados)
    servo_names = ["Cadera_Izq", "Cadera_Der", "Rodilla_Izq", 
                   "Rodilla_Der", "Pie_Izq", "Pie_Der"]
    
    for i, name in enumerate(servo_names):
        cv2.createTrackbar(name, "Biped Camera + Control", 90, 180, lambda x: None)
    
    print("\n" + "="*50)
    print("✅ SISTEMA LISTO - CONTROLES ACTIVOS")
    print("="*50)
    print("Teclado:")
    print("  [i] Modo IDLE (detener)")
    print("  [w] Modo WALK (caminar automático)")
    print("  [m] Modo MANUAL (control con sliders)")
    print("  [q] Salir")
    print("\nSliders: Arrastra para mover cada servo (0-180°)")
    print("="*50 + "\n")
    
    last_mode = "idle"
    last_servo_send = time.time()
    
    while True:
        # Obtener frame de la cámara
        frame = controller.get_frame()
        
        # Crear imagen combinada (video + panel de control)
        combined = np.zeros((780, 640, 3), dtype=np.uint8)
        
        if frame is not None:
            combined[0:480, 0:640] = frame
            control_panel_copy = control_panel.copy()
            
            # Mostrar ángulos actuales en el panel
            for i, name in enumerate(servo_names):
                angle = controller.servo_angles[i]
                cv2.putText(control_panel_copy, f"{angle:>3}°", 
                           (450, 60 + i*35), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, (0, 255, 255), 1)
            
            combined[480:780, 0:640] = control_panel_copy
        else:
            # Mensaje de "no video"
            cv2.putText(combined, "NO VIDEO", (200, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
        
        # Mostrar modo actual
        mode_text = f"MODO: {controller.mode.upper()}"
        cv2.putText(combined, mode_text, (10, 460), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Teclado
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord('i'):
            if last_mode != "idle":
                controller.send_command("set_mode", {"mode": "idle"})
                print("Modo: IDLE")
                last_mode = "idle"
        elif key == ord('w'):
            if last_mode != "walk":
                controller.send_command("set_mode", {"mode": "walk"})
                print("Modo: WALK - Caminando automático")
                last_mode = "walk"
        elif key == ord('m'):
            if last_mode != "manual":
                controller.send_command("set_mode", {"mode": "manual"})
                print("Modo: MANUAL - Usa sliders")
                last_mode = "manual"
        elif key == ord('q'):
            break
        
        # Modo manual: enviar posiciones de sliders
        if controller.mode == "manual":
            if time.time() - last_servo_send > 0.1:  # Enviar cada 100ms
                for i, name in enumerate(servo_names):
                    angle = cv2.getTrackbarPos(name, "Biped Camera + Control")
                    if abs(angle - controller.servo_angles[i]) > 2:
                        controller.send_command("set_servo", {"id": i, "angle": angle})
                last_servo_send = time.time()
        
        # Mostrar frame combinado
        cv2.imshow("Biped Camera + Control", combined)
    
    controller.running = False
    cv2.destroyAllWindows()
    print("\n✅ Sistema detenido correctamente")

if __name__ == "__main__":
    main()