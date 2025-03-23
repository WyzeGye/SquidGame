import json
import time
import serial
import pygame
from threading import Thread
import RPi.GPIO as GPIO

# Constants
TARGET_AFR_EFFICIENCY = 14.7
TARGET_AFR_PERFORMANCE = 12.5
COLD_START_TEMP = 20  # Below this temperature, use cold start enrichment
FUEL_MAP_FILE_EFFICIENCY = "fuel_map_efficiency.json"
FUEL_MAP_FILE_PERFORMANCE = "fuel_map_performance.json"
STAGES = [
    {"resolution": 15, "threshold": 0.1},
    {"resolution": 20, "threshold": 0.1},
    {"resolution": 25, "threshold": 0.1},
]
DYNO_MODE_BUTTON_PIN = 23  # GPIO pin for dyno mode button
BATTERY_VOLTAGE_PIN = 24  # GPIO pin for battery voltage monitoring
MAX_CYLINDERS = 4  # Maximum number of cylinders supported

# Initialize UART communication with ESP32s
uart_sensor = serial.Serial("/dev/ttyUSB0", 115200, timeout=0)  # ESP32 #1 (Sensors)
uart_actuator = serial.Serial("/dev/ttyUSB1", 115200, timeout=0)  # ESP32 #2 (Actuators)
uart_backup = serial.Serial("/dev/ttyUSB2", 115200, timeout=0)  # ESP32 #3 (Backup)

# Initialize display
pygame.init()
screen = pygame.display.set_mode((1280, 360))
pygame.display.set_caption("Motorcycle ECU")
font = pygame.font.Font(None, 74)  # Large readable text

# Initialize GPIO for dyno mode button and battery voltage
GPIO.setmode(GPIO.BCM)
GPIO.setup(DYNO_MODE_BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BATTERY_VOLTAGE_PIN, GPIO.IN)

# Load or initialize fuel maps
def load_fuel_map(mode, cylinder=1):
    file = f"fuel_map_{mode}_cylinder_{cylinder}.json"
    try:
        with open(file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return initialize_default_fuel_map(mode, cylinder)

def initialize_default_fuel_map(mode, cylinder):
    resolution = STAGES[0]["resolution"]
    fuel_map = {
        "resolution": resolution,
        "rpm_range": [1000, 6500],
        "map_range": [20, 100],
        "values": [[2.0 + 0.2 * i + 0.2 * j for j in range(resolution)] for i in range(resolution)],
        "dyno_learned": False,
    }
    save_fuel_map(fuel_map, mode, cylinder)
    return fuel_map

def save_fuel_map(fuel_map, mode, cylinder):
    file = f"fuel_map_{mode}_cylinder_{cylinder}.json"
    with open(file, "w") as f:
        json.dump(fuel_map, f)

# Self-learning algorithm
def self_learning_algorithm(fuel_map, measured_afr, rpm, map_value, target_afr, dyno_data=None):
    error = target_afr - measured_afr
    rpm_index = int((rpm - fuel_map["rpm_range"][0]) / (fuel_map["rpm_range"][1] - fuel_map["rpm_range"][0]) * fuel_map["resolution"])
    map_index = int((map_value - fuel_map["map_range"][0]) / (fuel_map["map_range"][1] - fuel_map["map_range"][0]) * fuel_map["resolution"])

    Kp = 0.01  # Proportional gain
    new_value = fuel_map["values"][rpm_index][map_index] + Kp * error

    if dyno_data:
        hp = dyno_data["hp"]
        torque = dyno_data["torque"]
        if performance_mode:
            new_value += 0.01 * (hp + torque)  # Optimize for HP and torque
        else:
            new_value += 0.01 * (torque - measured_afr)  # Optimize for torque and fuel economy

    # Validate AFR within safe limits
    new_value = max(1.0, min(20.0, new_value))  # AFR between 10:1 and 20:1
    fuel_map["values"][rpm_index][map_index] = new_value
    return fuel_map

# Read sensor data from ESP32 #1
def read_sensor_data():
    if uart_sensor.in_waiting > 0:
        data = uart_sensor.readline().decode("utf-8").strip()
        return json.loads(data)
    return None

# Send actuator commands to ESP32 #2
def send_actuator_commands(cylinder, injector_pulse, ignition_advance):
    command = json.dumps({"cylinder": cylinder, "injector": injector_pulse, "ignition": ignition_advance})
    uart_actuator.write(command.encode("utf-8"))

# Check for ESP32 failures
def check_esp32_failures():
    if uart_sensor.in_waiting == 0 or uart_actuator.in_waiting == 0:
        uart_backup.write(b"take_over")
        print("ESP32 failure detected. Switching to backup.")

# Update display
def update_display(rpm, mode, stage, afr, engine_temp, battery_voltage, dyno_mode=False, dyno_learned=False):
    screen.fill((255, 255, 255))  # White background
    text_rpm = font.render(f"RPM: {rpm}", True, (0, 0, 0))
    text_mode = font.render(f"Mode: {mode.capitalize()}", True, (0, 0, 0))
    text_stage = font.render(f"Stage: {stage}{' (DM)' if dyno_learned else ''}", True, (0, 0, 0))
    text_afr = font.render(f"AFR: {afr}", True, (0, 0, 0))
    text_temp = font.render(f"Temp: {engine_temp}°C", True, (0, 0, 0))
    text_battery = font.render(f"Battery: {battery_voltage}V", True, (0, 0, 0))

    if dyno_mode:
        text_dyno = font.render("Dyno Mode Active", True, (255, 0, 0))
        screen.blit(text_dyno, (700, 150))

    screen.blit(text_rpm, (50, 50))
    screen.blit(text_mode, (50, 150))
    screen.blit(text_stage, (50, 250))
    screen.blit(text_afr, (700, 50))
    screen.blit(text_temp, (700, 150))
    screen.blit(text_battery, (700, 250))
    pygame.display.flip()

# Check dyno mode button
def check_dyno_mode_button():
    if GPIO.input(DYNO_MODE_BUTTON_PIN) == GPIO.LOW:
        time.sleep(10)  # Hold button for 10 seconds
        if GPIO.input(DYNO_MODE_BUTTON_PIN) == GPIO.LOW:
            return True
    return False

# Read battery voltage
def read_battery_voltage():
    raw_value = GPIO.input(BATTERY_VOLTAGE_PIN)
    return raw_value * (5.0 / 1023.0) * 3  # Scale to actual voltage

# Detect connected actuators
def detect_connected_actuators():
    # Send a test signal to each actuator pin and check for a response
    connected_cylinders = []
    for cylinder in range(1, MAX_CYLINDERS + 1):
        injector_pin = 8 + cylinder  # Injector pins: D9-D12
        ignition_pin = 12 + cylinder  # Ignition pins: D13-D16
        if check_actuator_connection(injector_pin) and check_actuator_connection(ignition_pin):
            connected_cylinders.append(cylinder)
    return connected_cylinders

def check_actuator_connection(pin):
    # Implement code for checking actuator connection
    return True  # Assume all actuators are connected for now

# Main loop
def main():
    fuel_maps = [load_fuel_map("efficiency", i + 1) for i in range(MAX_CYLINDERS)]
    performance_mode = False
    current_stage = 0
    green_led_on = False
    dyno_mode = False
    dyno_learned = False
    connected_cylinders = detect_connected_actuators()

    while True:
        check_esp32_failures()

        if not dyno_mode and check_dyno_mode_button():
            dyno_mode = True
            print("Dyno Mode Activated")

        sensor_data = read_sensor_data()
        if sensor_data:
            rpm = sensor_data["rpm"]
            map_value = sensor_data["map"]
            afr = sensor_data["afr"]
            engine_temp = sensor_data["engine_temp"]
            dyno_data = sensor_data.get("dyno_data")
            battery_voltage = read_battery_voltage()

            if engine_temp < COLD_START_TEMP:
                injector_pulse = fuel_maps[0]["values"][0][0] * 1.2  # Cold start enrichment
            else:
                injector_pulse = fuel_maps[0]["values"][0][0]

            target_afr = TARGET_AFR_PERFORMANCE if performance_mode else TARGET_AFR_EFFICIENCY
            for cylinder in connected_cylinders:
                fuel_maps[cylinder - 1] = self_learning_algorithm(fuel_maps[cylinder - 1], afr, rpm, map_value, target_afr, dyno_data)
                send_actuator_commands(cylinder, injector_pulse, 10)  # Send commands to each connected cylinder

            if time.time() % 10 == 0:
                for cylinder in connected_cylinders:
                    save_fuel_map(fuel_maps[cylinder - 1], "efficiency", cylinder)
                    save_fuel_map(fuel_maps[cylinder - 1], "performance", cylinder)

            update_display(rpm, "performance" if performance_mode else "efficiency", f"{current_stage + 1}", afr, engine_temp, battery_voltage, dyno_mode, dyno_learned)

        if not check_12v_power():
            for cylinder in connected_cylinders:
                save_fuel_map(fuel_maps[cylinder - 1], "efficiency", cylinder)
                save_fuel_map(fuel_maps[cylinder - 1], "performance", cylinder)
            perform_graceful_shutdown()

        if not green_led_on:
            illuminate_green_led()
            green_led_on = True

        time.sleep(0.001)

# Failsafes
def check_12v_power():
    return True  # Replace with actual implementation

def perform_graceful_shutdown():
    print("Performing graceful shutdown...")
    time.sleep(1)
    exit()

def illuminate_green_led():
    print("System ready.")

if __name__ == "__main__":
    main()
