#include <ArduinoBLE.h>
#include <Arduino_LSM9DS1.h>  // Library for IMU (gyroscope, accelerometer, magnetometer)
#include <PulseSensorPlayground.h> 

// BLE Service and Characteristic UUIDs
BLEService sensorService("180C");
BLECharacteristic sensorDataChar("2A56", BLERead | BLENotify, 20);  // 20 bytes limit

//  PulseSensor Variables
PulseSensorPlayground pulseSensor;  // Creates an instance of the PulseSensorPlayground object called "pulseSensor"

const int PULSE_WIRE = 0;       // PulseSensor PURPLE WIRE connected to ANALOG PIN 0
const int THRESHOLD = 600;           // Determine which Signal to "count as a beat" and which to ignore.
                               // Use the "Gettting Started Project" to fine-tune Threshold Value beyond default setting.
                               // Otherwise leave the default "550" value. 

unsigned long startTime = 0;                               

int Signal, sensor_BPM = 0;
unsigned long IBI = 0;
unsigned long beatTimeout = 1000; // Timeout period before resetting myBPM to 0.
unsigned long currentTime = 0;
unsigned long lastBeatTime = 0; // Time of last detected beat.

void setup() {
  Serial.begin(115200);
  //while (!Serial);

  if (!BLE.begin()) {
    Serial.println("Starting BLE failed!");
    while (1);
  }

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  // Double-check the "pulseSensor" object was created and "began" seeing a signal. 
  if (!pulseSensor.begin()) {
    Serial.println("Failed to create PulseSensor object.");  //This prints one time at Arduino power-up,  or on Arduino reset.  
  }

  startTime = millis();
  BLE.setLocalName("Nano33BLE");
  BLE.setAdvertisedService(sensorService);
  sensorService.addCharacteristic(sensorDataChar);
  BLE.addService(sensorService);
  BLE.advertise();

  Serial.println("BLE device is now advertising...");
}

void getBPM() {
  currentTime = millis();

  Signal = analogRead(PULSE_WIRE);

  if (currentTime - lastBeatTime > beatTimeout) { sensor_BPM = 0; }
  
  if (Signal > THRESHOLD) {
    if (currentTime - lastBeatTime > 300) {
      IBI = currentTime - lastBeatTime;
      lastBeatTime = currentTime;
      sensor_BPM = 60000 / IBI;
    }
  }
}

void loop() {
  BLEDevice central = BLE.central();

  if (central) {
    Serial.print( F ( "Connected to central: " ) );
    Serial.println( central.address() );

    while (central.connected()) {
      currentTime = millis();
      float ax, ay, az;

      if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable() && IMU.magneticFieldAvailable()) {
        IMU.readAcceleration(ax, ay, az);
        getBPM();

        // Data encoding into 20 bytes
        uint8_t data[12];
        uint32_t time = (uint32_t)(currentTime - startTime);
        int16_t accelX = (int16_t)(ax * 1000);  // Convert to int and scale
        int16_t accelY = (int16_t)(ay * 1000);
        int16_t accelZ = (int16_t)(az * 1000);
        int16_t bpm = (int16_t) sensor_BPM;
        
        // Pack data into bytes (6x3 bytes = 18, plus padding if needed)
        memcpy(data, &time, 4);
        memcpy(data + 4, &accelX, 2);
        memcpy(data + 6, &accelY, 2);
        memcpy(data + 8, &accelZ, 2);
        memcpy(data + 10, &bpm, 2); 

        // Send data over BLE
        sensorDataChar.writeValue(data, 12);  // Send 18 bytes (6*3 sensors data)

        delay(50);  // Adjust delay as needed
      }
    }
    Serial.println("Disconnected from Central.");

  }
}
