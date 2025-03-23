#include <Arduino.h>
#include <HardwareSerial.h>

// Pin definitions
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
    DynamicJsonDocument doc(128);
    deserializeJson(doc, command);

    int cylinder = doc["cylinder"];
    float injector_pulse = doc["injector"];
    float ignition_advance = doc["ignition"];

    switch (cylinder) {
      case 1:
        control_injector(INJECTOR_PIN_1, injector_pulse);
        control_ignition(IGNITION_PIN_1, ignition_advance);
        break;
      case 2:
        control_injector(INJECTOR_PIN_2, injector_pulse);
        control_ignition(IGNITION_PIN_2, ignition_advance);
        break;
      case 3:
        control_injector(INJECTOR_PIN_3, injector_pulse);
        control_ignition(IGNITION_PIN_3, ignition_advance);
        break;
      case 4:
        control_injector(INJECTOR_PIN_4, injector_pulse);
        control_ignition(IGNITION_PIN_4, ignition_advance);
        break;
    }
  }
}

void control_injector(int pin, float pulse_width) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(pulse_width * 1000);  # Convert ms to µs
  digitalWrite(pin, LOW);
}

void control_ignition(int pin, float advance) {
  digitalWrite(pin, HIGH);
  delayMicroseconds(advance * 1000);  # Convert degrees to µs
  digitalWrite(pin, LOW);
}
