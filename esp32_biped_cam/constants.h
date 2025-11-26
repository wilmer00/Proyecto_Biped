#ifndef CONSTANTS_H
#define CONSTANTS_H

// ==================== CONFIGURACIÓN WIFI ====================
#define WIFI_SSID "Redmi"
#define WIFI_PASSWORD "qwerty123"

// ==================== CONFIGURACIÓN DE SERVOS ====================
// Offsets para alineación mecánica (ajústalos después de calibrar)
#define LEFT_HIP_OFFSET    0
#define RIGHT_HIP_OFFSET   0
#define LEFT_KNEE_OFFSET   0
#define RIGHT_KNEE_OFFSET  0
#define LEFT_FOOT_OFFSET   0
#define RIGHT_FOOT_OFFSET  0

// ==================== DIMENSIONES DEL BÍPEDO ====================
#define L1  45.0  // Distancia Cadera-Rodilla (mm)
#define L2  55.0  // Distancia Rodilla-Tobillo (mm)

// ==================== PARÁMETROS DE MARCHA ====================
#define STEP_CLEARANCE  20  // Altura levanta pie (mm)
#define STEP_HEIGHT     85  // Altura cadera desde suelo (mm)
#define STEP_LENGTH     30  // Longitud del paso (mm)
#define STEP_DURATION   800 // Milisegundos por paso

// ==================== PINES Y DIRECCIÓN I2C ====================
#define I2C_SDA 13
#define I2C_SCL 12
#define PCA9685_ADDR 0x40  // Dirección del PCA9685

// ==================== PINES CÁMARA ESP32-CAM ====================
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

#endif