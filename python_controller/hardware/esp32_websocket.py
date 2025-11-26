"""
Comunicación WebSocket con ESP32
"""
import json
import threading
import time
from websocket import create_connection, WebSocketConnectionClosedException
from config.settings import Config


class ESP32WebSocket:
    def __init__(self, ip=None, port=None):
        self.ip = ip or Config.ESP32_IP
        self.port = port or Config.WEBSOCKET_PORT
        self.ws_url = f"ws://{self.ip}:{self.port}"
        self.ws = None
        self.connected = False
        self.running = False
        self.thread = None
        
        # Estado recibido del ESP32
        self.mode = "idle"
        self.servo_angles = [Config.SERVO_DEFAULT_ANGLE] * Config.NUM_SERVOS
        self.sensor_data = {}
        
        # Callbacks
        self.on_state_update = None
        
    def start(self):
        """Iniciar conexión WebSocket"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._ws_loop, daemon=True)
        self.thread.start()
        print(f"📡 WebSocket iniciado: {self.ws_url}")
        
    def stop(self):
        """Detener conexión"""
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        if self.thread:
            self.thread.join(timeout=2)
        print("📡 WebSocket detenido")
        
    def _ws_loop(self):
        """Loop principal de WebSocket"""
        retry_delay = 2
        
        while self.running:
            try:
                self.ws = create_connection(self.ws_url, timeout=3)
                self.connected = True
                print("✅ WebSocket conectado")
                
                while self.running and self.connected:
                    try:
                        # Recibir mensajes del ESP32
                        message = self.ws.recv()
                        if message:
                            self._process_message(message)
                            
                    except WebSocketConnectionClosedException:
                        print("⚠️ WebSocket desconectado")
                        self.connected = False
                        break
                        
                    except Exception as e:
                        # Timeout normal, continuar
                        pass
                        
            except Exception as e:
                if self.connected:
                    print(f"❌ WebSocket error: {e}")
                self.connected = False
                time.sleep(retry_delay)
                
    def _process_message(self, message):
        """Procesar mensajes recibidos del ESP32"""
        try:
            data = json.loads(message)
            
            if "mode" in data:
                self.mode = data["mode"]
                
            if "servos" in data:
                self.servo_angles = data["servos"]
                
            if "sensors" in data:
                self.sensor_data = data["sensors"]
                
            # Ejecutar callback si existe
            if self.on_state_update:
                self.on_state_update(data)
                
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON: {e}")
            
    def send_command(self, cmd, params=None):
        """Enviar comando al ESP32"""
        if not self.connected or not self.ws:
            return False
            
        try:
            payload = {"cmd": cmd}
            if params:
                payload.update(params)
                
            self.ws.send(json.dumps(payload))
            return True
            
        except Exception as e:
            print(f"Error enviando comando: {e}")
            self.connected = False
            return False
            
    def set_mode(self, mode):
        """Cambiar modo del robot"""
        return self.send_command("set_mode", {"mode": mode})
        
    def set_servo(self, servo_id, angle):
        """Mover un servo específico"""
        angle = max(Config.SERVO_MIN_ANGLE, min(Config.SERVO_MAX_ANGLE, angle))
        return self.send_command("set_servo", {"id": servo_id, "angle": angle})
        
    def set_all_servos(self, angles):
        """Mover todos los servos simultáneamente"""
        if len(angles) != Config.NUM_SERVOS:
            print(f"Error: Se esperaban {Config.NUM_SERVOS} ángulos")
            return False
        return self.send_command("set_all_servos", {"angles": angles})
        
    def get_state(self):
        """Obtener estado actual"""
        return {
            "connected": self.connected,
            "mode": self.mode,
            "servo_angles": self.servo_angles.copy(),
            "sensor_data": self.sensor_data.copy()
        }
        
    def is_connected(self):
        """Verificar conexión"""
        return self.connected