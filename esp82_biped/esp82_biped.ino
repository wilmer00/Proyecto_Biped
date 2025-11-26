#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(0x40);

#define SERVOMIN 150
#define SERVOMAX 600

void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando test de 6 servos con PCA9685 + ESP8266");

  // Pines oficiales del ESP8266
  // SDA = D2 (GPIO 4)
  // SCL = D1 (GPIO 5)
  Wire.begin(4, 5);

  pca.begin();
  pca.setPWMFreq(50);  // Frecuencia estándar de servos
  delay(10);
}

int angleToPulse(int angle) {
  return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void setServo(int channel, int angle) {
  angle = constrain(angle, 0, 180);
  int pulse = angleToPulse(angle);
  pca.setPWM(channel, 0, pulse);
  Serial.printf("Servo %d -> %d° (pulso %d)\n", channel, angle, pulse);
}

void testServo(int channel) {
  Serial.printf("\n--- Probando servo %d ---\n", channel);

  for (int a = 0; a <= 180; a += 10) {
    setServo(channel, a);
    delay(60);
  }
  delay(200);

  for (int a = 180; a >= 0; a -= 10) {
    setServo(channel, a);
    delay(60);
  }
  delay(300);
}

void loop() {

  // 🔹 Test 1: mover cada servo individualmente
  for (int s = 0; s < 6; s++) {
    testServo(s);
  }

  // 🔹 Test 2: mover los 6 servos juntos (sincronizados)
  Serial.println("\n--- Moviendo todos los servos juntos ---");
  
  for (int a = 0; a <= 180; a += 10) {
    for (int s = 0; s < 6; s++) {
      setServo(s, a);
    }
    delay(100);
  }
  delay(400);

  for (int a = 180; a >= 0; a -= 10) {
    for (int s = 0; s < 6; s++) {
      setServo(s, a);
    }
    delay(100);
  }
  delay(1000);

}
