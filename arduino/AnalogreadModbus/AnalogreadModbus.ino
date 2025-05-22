#include <ModbusRtu.h>

// Modbus slave ID
#define SLAVE_ID 2

// RE and DE pins for MAX485 (connect to separate Arduino pins)
#define RE_PIN 2
#define DE_PIN 3

// Holding registers (1 register untuk menyimpan data analog)
uint16_t holdingRegs[1]; // Array untuk menyimpan data analog

Modbus slave(SLAVE_ID, RE_PIN, DE_PIN); // Separate RE & DE pins

void setup() {
  // Initialize serial for RS485 (adjust baud rate as needed)
  Serial.begin(9600);
  slave.begin(9600);

  // Initialize control pins
  pinMode(RE_PIN, OUTPUT);
  pinMode(DE_PIN, OUTPUT);

  // Initialize analog pin (A0)
  pinMode(A0, INPUT);
}

void loop() {
  // Membaca nilai analog dari pin A0
  int analogValue = analogRead(A0);

  // Konversi nilai analog (0-1023) ke format 16-bit untuk holding register
  holdingRegs[0] = abs(analogValue-500);

  // Poll untuk menangani permintaan Modbus
  slave.poll(holdingRegs, sizeof(holdingRegs) / sizeof(holdingRegs[0]));
}