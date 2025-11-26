#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#define I2C_SDA 13
#define I2C_SCL 12
#define PCA9685_ADDR 0x40

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver(PCA9685_ADDR);

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== CALIBRACIÓN DE SERVOS ===");
  
  Wire.begin(I2C_SDA, I2C_SCL);
  pca.begin();
  pca.setPWMFreq(50);
  
  // Centrar todos los servos en 90°
  for(int i = 0; i < 6; i++) {
    int pulse = map(90, 0, 180, 150, 600);
    pca.setPWM(i, 0, pulse);
  }
  
  Serial.println("✅ Servos centrados en 90°");
  Serial.println("1. Alinea mecánicamente las piernas");
  Serial.println("2. Anota desviación (grados)");
  Serial.println("3. Edita offsets en constants.h");
}

void loop() {
  // Los servos se quedan en 90° indefinidamente
}