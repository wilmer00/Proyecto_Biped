#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <WebSocketsServer.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <ArduinoJson.h>

// ==================== ✅ CONFIGURACIÓN WIFI (TU MÓVIL) ====================
#define WIFI_SSID "Redmi"          // Nombre de tu hotspot
#define WIFI_PASSWORD "qwerty123" // Contraseña de tu hotspot

// ==================== CONFIGURACIÓN HARDWARE ====================
#define I2C_SDA 13
#define I2C_SCL 12
#define PCA9685_ADDR 0x40
#define LED_PIN 2

// Dimensiones de las piernas (en mm)
#define L1 45.0  // Longitud del fémur
#define L2 55.0  // Longitud de la tibia

// Offsets para calibración
#define LEFT_HIP_OFFSET    0
#define RIGHT_HIP_OFFSET   0
#define LEFT_KNEE_OFFSET   0
#define RIGHT_KNEE_OFFSET  0
#define LEFT_FOOT_OFFSET   0
#define RIGHT_FOOT_OFFSET  0

// Parámetros de marcha
#define STEP_CLEARANCE 20
#define STEP_HEIGHT 85
#define STEP_LENGTH 30
#define STEP_DURATION 800

// Pines de la cámara OV2640 (AI-Thinker)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ==================== OBJETOS GLOBALES ====================
Adafruit_PWMServoDriver pca(PCA9685_ADDR);
WebServer server(80);
WebSocketsServer webSocket(82);

enum Mode { MODE_IDLE, MODE_WALK, MODE_MANUAL };
Mode currentMode = MODE_IDLE;
unsigned long lastStepTime = 0;
int servoAngles[6] = {90, 90, 90, 90, 90, 90};

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.println("\n🤖 Iniciando Bípedo ESP32-S...");
  Serial.print("Conectando a WiFi: ");
  Serial.println(WIFI_SSID);
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Inicializar PCA9685
  Wire.begin(I2C_SDA, I2C_SCL);
  pca.begin();
  pca.setPWMFreq(50);
  
  // Inicializar cámara
  if (!initCamera()) {
    Serial.println("❌ FALLA CÁMARA: Revisar conexión física");
    while(1) {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      delay(100);
    }
  }
  
  // ✅ MODO STATION: Se conecta al hotspot del móvil
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n✅ Conectado al WiFi!");
  Serial.print("IP del ESP32: ");
  Serial.println(WiFi.localIP());
  
  // Configurar servidor HTTP (video) y WebSocket (control)
  server.on("/", handleRoot);
  server.on("/status", handleStatus);
  server.begin();
  
  webSocket.begin();
  webSocket.onEvent(handleWebSocketEvent);
  
  standStraight();
  delay(500);
}

// ==================== INICIALIZACIÓN DE CÁMARA ====================
bool initCamera() {
  delay(2000);
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  
  config.xclk_freq_hz = 10000000;      // 10MHz para estabilidad
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;  // 320x240
  config.jpeg_quality = 20;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  
  esp_err_t err = esp_camera_init(&config);
  
  if (err == ESP_OK) {
    Serial.println("✅ Cámara OV2640 inicializada");
    return true;
  }
  
  Serial.printf("❌ Error cámara: 0x%x\n", err);
  return false;
}

// ==================== LOOP PRINCIPAL ====================
void loop() {
  server.handleClient();
  webSocket.loop();
  
  if (currentMode == MODE_WALK) walkCycle();
  
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 500) {
    sendStatus();
    lastStatus = millis();
  }
}

// ==================== CINEMÁTICA DE MARCHA ====================
void walkCycle() {
  if (millis() - lastStepTime < STEP_DURATION) return;
  lastStepTime = millis();
  static float phase = 0.0;
  phase += 0.1;
  if (phase > 1.0) phase = 0.0;
  
  if (phase < 0.5) {
    moveLeg(0, phase * 2.0);  // Pierna izquierda
    holdLeg(3);                // Pierna derecha fija
  } else {
    moveLeg(3, (phase - 0.5) * 2.0);  // Pierna derecha
    holdLeg(0);                        // Pierna izquierda fija
  }
}

void moveLeg(int baseChannel, float progress) {
  float x = STEP_LENGTH * sin(progress * PI);
  float z = STEP_HEIGHT - STEP_CLEARANCE * sin(progress * PI);
  float r = sqrt(x*x + z*z);
  float gamma = atan2(z, x);
  
  // ✅ CORREGIDO: L1 y L2 están definidos arriba
  float cos_knee = constrain((L1*L1 + L2*L2 - r*r) / (2*L1*L2), -1.0, 1.0);
  float knee = acos(cos_knee) * 180.0 / PI;
  float alpha = asin((L2 * sin(acos(cos_knee))) / r) * 180.0 / PI;
  float hip = gamma * 180.0 / PI - alpha;
  float foot = -(hip + knee);
  
  setServo(baseChannel, 90 + hip);
  setServo(baseChannel + 1, 90 + knee);
  setServo(baseChannel + 2, 90 + foot);
}

void holdLeg(int baseChannel) {
  setServo(baseChannel, 90);
  setServo(baseChannel + 1, 90);
  setServo(baseChannel + 2, 90);
}

void standStraight() {
  for (int i = 0; i < 6; i++) setServo(i, 90);
}

void setServo(int channel, int angle) {
  angle = constrain(angle, 0, 180);
  servoAngles[channel] = angle;
  int pulse = map(angle, 0, 180, 150, 600);
  pca.setPWM(channel, 0, pulse);
}

// ==================== WEBSOCKET ====================
void handleWebSocketEvent(uint8_t num, WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("❌ Cliente %u desconectado\n", num);
      digitalWrite(LED_PIN, LOW);
      break;
    case WStype_CONNECTED:
      Serial.printf("✅ Cliente %u conectado\n", num);
      digitalWrite(LED_PIN, HIGH);
      break;
    case WStype_TEXT: {
      String message = String((char*)payload);
      DynamicJsonDocument doc(128);
      deserializeJson(doc, message);
      String cmd = doc["cmd"];
      
      if (cmd == "set_mode") {
        String mode = doc["mode"];
        if (mode == "walk") currentMode = MODE_WALK;
        else if (mode == "manual") currentMode = MODE_MANUAL;
        else currentMode = MODE_IDLE;
        standStraight();
      } else if (cmd == "set_servo") {
        if (currentMode == MODE_MANUAL) {
          setServo(doc["id"], doc["angle"]);
        }
      }
      break;
    }
    default: break;
  }
}

void sendStatus() {
  if (webSocket.connectedClients() < 1) return;
  
  String json = "{";
  json += "\"mode\":\"" + String(currentMode == MODE_IDLE ? "idle" : 
                                 currentMode == MODE_WALK ? "walk" : "manual") + "\",";
  json += "\"servos\":[" + String(servoAngles[0]) + ",";
  json += String(servoAngles[1]) + "," + String(servoAngles[2]) + ",";
  json += String(servoAngles[3]) + "," + String(servoAngles[4]) + ",";
  json += String(servoAngles[5]) + "]";
  json += "}";
  webSocket.broadcastTXT(json);
}

// ==================== HTTP VIDEO STREAM ====================
void handleRoot() {
  WiFiClient client = server.client();
  
  // Encabezados HTTP para video streaming
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n";
  response += "Cache-Control: no-cache, no-store, must-revalidate\r\n";
  response += "Pragma: no-cache\r\n";
  response += "Expires: 0\r\n";
  response += "Access-Control-Allow-Origin: *\r\n";
  response += "Connection: keep-alive\r\n\r\n";
  
  client.write(response.c_str(), response.length());
  Serial.println("📹 Cliente de video conectado");
  
  while (client.connected()) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Error obteniendo frame");
      delay(10);  // ✅ CORREGIDO: delay() en lugar de time.sleep()
      continue;
    }
    
    String header = "--frame\r\n";
    header += "Content-Type: image/jpeg\r\n";
    header += "Content-Length: " + String(fb->len) + "\r\n\r\n";
    
    client.write(header.c_str(), header.length());
    client.write(fb->buf, fb->len);
    client.write("\r\n", 2);
    
    esp_camera_fb_return(fb);
    yield(); // Para evitar watchdog
  }
  
  Serial.println("📹 Cliente de video desconectado");
}

void handleStatus() {
  String json = "{\"status\":\"ok\",\"ip\":\"" + WiFi.localIP().toString() + "\"}";
  server.send(200, "application/json", json);
}

void handleNotFound() {
  server.send(404, "text/plain", "Not Found");
}