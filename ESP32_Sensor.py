#include <Arduino.h>
#include <HardwareSerial.h>

// Pin definitions
#define O2_SENSOR_PIN A0
#define MAP_SENSOR_PIN A1
#define TPS_PIN A2
#define CRANKSHAFT_PIN 2
#define ENGINE_TEMP_PIN A3

void setup() {
  Serial.begin(115200);
  pinMode(O2_SENSOR_PIN, INPUT);
  pinMode(MAP_SENSOR_PIN, INPUT);
  pinMode(TPS_PIN, INPUT);
  pinMode(CRANKSHAFT_PIN, INPUT);
  pinMode(ENGINE_TEMP_PIN, INPUT);
}

void loop() {
  // Read sensor data
  float rpm = read_rpm();
  float map_value = read_map();
  float afr = read_afr();
  float engine_temp = read_engine_temp();

  // Send data to CM4
  String data = "{\"rpm\":" + String(rpm) + ",\"map\":" + String(map_value) + ",\"afr\":" + String(afr) + ",\"engine_temp\":" + String(engine_temp) + "}";
  Serial.println(data);

  delay(1);  // Minimize latency
}

float read_rpm() {
  // Measure RPM from crankshaft sensor
  unsigned long pulse_time = pulseIn(CRANKSHAFT_PIN, HIGH);
  return pulse_time > 0 ? 60000000 / (pulse_time * 360) : 0;  // 360 pulses per revolution
}

float read_map() {
  // Read MAP sensor (0-5V to 0-100 kPa)
  return analogRead(MAP_SENSOR_PIN) * (100.0 / 1023.0);
}

float read_afr() {
  // Read O2 sensor (0-5V to 10-20 AFR)
  return analogRead(O2_SENSOR_PIN) * (10.0 / 1023.0) + 10;
}

float read_engine_temp() {
  // Read engine block temperature (NTC thermistor)
  int raw = analogRead(ENGINE_TEMP_PIN);
  float resistance = 10000.0 / (1023.0 / raw - 1);  // 10k pull-up resistor
  float temp = 1 / (log(resistance / 10000) / 3950 + 1 / 298.15) - 273.15;  // Steinhart-Hart equation
  return temp;
}
