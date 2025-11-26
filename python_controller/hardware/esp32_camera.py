"""
Gestión de la cámara ESP32-CAM
"""
import cv2
import numpy as np
import threading
import time
from config.settings import Config


class ESP32Camera:
    def __init__(self, ip=None):
        self.ip = ip or Config.ESP32_IP
        self.stream_url = Config.STREAM_URL_TEMPLATE.format(ip=self.ip)
        self.frame = None
        self.running = False
        self.connected = False
        self.lock = threading.Lock()
        self.frame_count = 0
        self.thread = None
        
    def start(self):
        """Iniciar el stream de la cámara"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._video_loop, daemon=True)
        self.thread.start()
        print(f"📹 Cámara iniciada: {self.stream_url}")
        
    def stop(self):
        """Detener el stream"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("📹 Cámara detenida")
        
    def _video_loop(self):
        """Loop principal del stream de video"""
        retry_delay = 2
        
        while self.running:
            cap = None
            try:
                cap = cv2.VideoCapture(self.stream_url)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if not cap.isOpened():
                    print(f"❌ Stream no disponible, reintentando en {retry_delay}s...")
                    time.sleep(retry_delay)
                    continue
                
                print("✅ Stream de video conectado")
                self.connected = True
                
                while self.running:
                    ret, frame = cap.read()
                    
                    if ret and frame is not None:
                        with self.lock:
                            self.frame = cv2.resize(
                                frame, 
                                (Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT)
                            )
                            self.frame_count += 1
                    else:
                        # Frame perdido, esperar un poco
                        time.sleep(0.05)
                        
            except Exception as e:
                print(f"❌ Error en video stream: {e}")
                self.connected = False
                time.sleep(retry_delay)
                
            finally:
                if cap:
                    cap.release()
                    
    def get_frame(self):
        """Obtener el frame actual de forma segura"""
        with self.lock:
            if self.frame is not None:
                return self.frame.copy()
            return None
            
    def is_connected(self):
        """Verificar si está conectado"""
        return self.connected
    
    def get_stats(self):
        """Obtener estadísticas de la cámara"""
        return {
            "connected": self.connected,
            "frame_count": self.frame_count,
            "url": self.stream_url
        }