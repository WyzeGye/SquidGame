#include <Arduino.h>
#include <HardwareSerial.h>

// Pin definitions (same as ESP32 #1 and #2)
#define O2_SENSOR_PIN A0
#define MAP_SENSOR_PIN A1
#define TPS_PIN A2
#define CRANKSHAFT_PIN 2
#define ENGINE_TEMP_PIN A3
#define INJECTOR_PIN_1 9
#define IGNITION_PIN_1 10
#define INJECTOR_PIN_2 11
#define IGNITION_PIN_2 12
#define INJECTOR_PIN_3 13
#define IGNITION_PIN_3 14
#define INJECTOR_PIN_4 15
#define IGNITION_PIN_4 16

void setup() {
  Serial.begin(115200);
  pinMode(O2_SENSOR_PIN, INPUT);
  pinMode(MAP_SENSOR_PIN, INPUT);
  pinMode(TPS_PIN, INPUT);
  pinMode(CRANKSHAFT_PIN, INPUT);
  pinMode(ENGINE_TEMP_PIN, INPUT);
  pinMode(INJECTOR_PIN_1, OUTPUT);
  pinMode(IGNITION_PIN_1, OUTPUT);
  pinMode(INJECTOR_PIN_2, OUTPUT);
  pinMode(IGNITION_PIN_2, OUTPUT);
  pinMode(INJECTOR_PIN_3, OUTPUT);
  pinMode(IGNITION_PIN_3, OUTPUT);
  pinMode(INJECTOR_PIN_4, OUTPUT);
  pinMode(IGNITION_PIN_4, OUTPUT);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (command == "take_over_sensor") {
      // Take over sensor role
      float rpm = read_rpm();
      float map_value = read_map();
      float afr = read_afr();
      float engine_temp = read_engine_temp();
      String data = "{\"rpm\":" + String(rpm) + ",\"map\":" + String(map_value) + ",\"afr\":" + String(afr) + ",\"engine_temp\":" + String(engine_temp) + "}";
      Serial.println(data);
    } else if (command == "take_over_actuator") {
      // Take over actuator role
      if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        DynamicJsonDocument doc(128);
        deserializeJson(doc, command);
        int cylinder = doc["cylinder"];
        float injector_pulse = doc["injector"];
        float ignition_advance = doc["ignition"];
        control_injector(cylinder, injector_pulse);
        control_ignition(cylinder, ignition_advance);
      }
    }
  }
}

// Sensor functions (same as ESP32 #1)
float read_rpm() {
  unsigned long pulse_time = pulseIn(CRANKSHAFT_PIN, HIGH);
  return pulse_time > 0 ? 60000000 / (pulse_time * 360) : 0;
}

float read_map() {
  return analogRead(MAP_SENSOR_PIN) * (100.0 / 1023.0);
}

float read_afr() {
  return analogRead(O2_SENSOR_PIN) * (10.0 / 1023.0) + 10;
}

float read_engine_temp() {
  int raw = analogRead(ENGINE_TEMP_PIN);
  float resistance = 10000.0 / (1023.0 / raw - 1);
  float temp = 1 / (log(resistance / 10000) / 3950 + 1 / 298.15) - 273.15;
  return temp;
}

// Actuator functions (same as ESP32 #2)
void control_injector(int cylinder, float pulse_width) {
  int pin;
  switch (cylinder) {
    case 1: pin = INJECTOR_PIN_1; break;
    case 2: pin = INJECTOR_PIN_2; break;
    case 3: pin = INJECTOR_PIN_3; break;
    case 4: pin = INJECTOR_PIN_4; break;
  }
  digitalWrite(pin, HIGH);
  delayMicroseconds(pulse_width * 1000);
  digitalWrite(pin, LOW);
}

void control_ignition(int cylinder, float advance) {
  int pin;
  switch (cylinder) {
    case 1: pin = IGNITION_PIN_1; break;
    case 2: pin = IGNITION_PIN_2; break;
    case 3: pin = IGNITION_PIN_3; break;
    case 4: pin = IGNITION_PIN_4; break;
  }
  digitalWrite(pin, HIGH);
  delayMicroseconds(advance * 1000);
  digitalWrite(pin, LOW);
}
