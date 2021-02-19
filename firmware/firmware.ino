#include <Wire.h>

static const int pin_manual_control_enable = 24;
static const int pin_pressure_vacuum = 25; 
static const int pin_analog_in = A12; // pin 26

static const int pin_LED_error = 23;
static const int pin_LED_1 = 22;

static const int pin_sensor_select = 15;

static const int pin_valve_C1 = 4;
static const int pin_valve_C2 = 5;
static const int pin_valve_C3 = 6;
static const int pin_valve_C4 = 7;
static const int pin_valve_C5 = 8;
static const int pin_valve_C6 = 9;
static const int pin_valve_C7 = 14;

const int check_manual_input_interval_us = 5000;
IntervalTimer Timer_check_manual_input;

volatile bool flag_check_manual_inputs = false;

bool flag_manual_control_enabled = false;
int mode_pressure_vacuum = 0; // 1: pressure, 0: vacuum
int analog_in = 0;
float disc_pump_power = 0;
bool disc_pump_enabled = false;

// disc pump communication
int number_of_attemps = 0;
#define UART_disc_pump Serial8
char disc_pump_rx_buffer[32];
int disc_pump_rx_ptr = 0;

// flow sensor, reference: https://github.com/Sensirion/arduino-liquid-flow-snippets/blob/master/SF06/example_19_DIY_flow_meter_SF06/example_19_DIY_flow_meter_SF06.ino
const int SLF3x_ADDRESS = 0x08;
const float SCALE_FACTOR_FLOW = 500.0; // Scale Factor for flow rate measurement
const float SCALE_FACTOR_TEMP = 200.0; // Scale Factor for temperature measurement
const char *UNIT_FLOW = " ml/min"; // physical unit of the flow rate measurement
const char *UNIT_TEMP = " deg C"; //physical unit of the temperature measurement
int ret;
int16_t signed_flow_value;
float scaled_flow_value;
byte sensor_flow_crc;

void setup() 
{
  // USB serial
  Serial.begin(2000000);
  delayMicroseconds(5000);
  Serial.println("Connected"); // not showing up
  
  pinMode(pin_manual_control_enable, INPUT_PULLUP);
  pinMode(pin_pressure_vacuum, INPUT);
  
  pinMode(pin_LED_error, OUTPUT);
  pinMode(pin_LED_1, OUTPUT);

  pinMode(pin_sensor_select, OUTPUT);

  pinMode(pin_valve_C1,OUTPUT);
  pinMode(pin_valve_C2,OUTPUT);
  pinMode(pin_valve_C3,OUTPUT);
  pinMode(pin_valve_C4,OUTPUT);
  pinMode(pin_valve_C5,OUTPUT);
  pinMode(pin_valve_C6,OUTPUT);
  pinMode(pin_valve_C7,OUTPUT);

  analogWriteResolution(10);
  
  // interval timer for checking manual input
  Timer_check_manual_input.begin(set_check_manual_input_flag,check_manual_input_interval_us);

  // disc pump serial
  UART_disc_pump.begin(115200);
  UART_disc_pump.print("#W1,1000\n"); // limit pump power to 1000 mW
  UART_disc_pump.print("#W10,0\n");
  UART_disc_pump.print("#W11,0\n");

  // I2C sensors
  Wire1.begin();
  
  select_sensor_2();
  /*
  // soft reset
  do {
    // Soft reset the sensor
    Wire1.beginTransmission(0x00);
    Wire1.write(0x06);
    ret = Wire1.endTransmission();
    if (ret != 0) {
      Serial.println("Error while sending soft reset command, retrying...");
      delay(500); // wait long enough for chip reset to complete
    }
  } while (ret != 0);
  */

  do {
    // Soft reset the sensor
    Wire1.beginTransmission(0x00);
    Wire1.write(0x06);
    ret = Wire1.endTransmission();
    if (ret != 0) {
      Serial.println("Error while sending soft reset command, retrying...");
      delay(500); // wait long enough for chip reset to complete
    }
  } while (ret != 0);

  do {
    // To perform a measurement, first send 0x3608 to switch to continuous
    Wire1.beginTransmission(SLF3x_ADDRESS);
    Wire1.write(0x36);
    Wire1.write(0x08);
    ret = Wire1.endTransmission();
    if (ret != 0) {
      Serial.println("Error starting measurement ...");
      delay(500); // wait long enough for chip reset to complete
    }
  } while (ret != 0);
  
}

void loop() {
  // put your main code here, to run repeatedly:

  if(flag_check_manual_inputs)
  {
    // check manual control
    flag_manual_control_enabled = 1 - digitalRead(pin_manual_control_enable);

    // if manual input is enabled, check mode (pressure vs vacuum) and analog_in, set the pump power accordingly
    if(flag_manual_control_enabled)
    {

      // set mode (pressure vs vacuum)
      mode_pressure_vacuum = digitalRead(pin_pressure_vacuum);
      if(mode_pressure_vacuum == 0 )
        set_mode_to_vacuum();
      else
        set_mode_to_pressure();

      // set pump power
      analog_in = analogRead(pin_analog_in);
      if(analog_in>23) // only enable the pump when the analog_in is > 23 (/1023)
      {
        disc_pump_power = analog_in - 23;
        disc_pump_enabled = true;
        set_disc_pump_power(disc_pump_power);
        set_disc_pump_enabled(disc_pump_enabled);
        analogWrite(pin_LED_1,disc_pump_power);
        analogWrite(pin_valve_C1,disc_pump_power);
        analogWrite(pin_valve_C2,disc_pump_power);
        analogWrite(pin_valve_C3,disc_pump_power);
        analogWrite(pin_valve_C4,disc_pump_power);
        analogWrite(pin_valve_C5,disc_pump_power);
        analogWrite(pin_valve_C6,disc_pump_power);
        analogWrite(pin_valve_C7,disc_pump_power);
      }
      else
      {
        disc_pump_power = 0;
        disc_pump_enabled = false;
        set_disc_pump_enabled(disc_pump_enabled);
        set_disc_pump_power(disc_pump_power);
        analogWrite(pin_LED_1,disc_pump_power);
        analogWrite(pin_valve_C1,disc_pump_power);
        analogWrite(pin_valve_C2,disc_pump_power);
        analogWrite(pin_valve_C3,disc_pump_power);
        analogWrite(pin_valve_C4,disc_pump_power);
        analogWrite(pin_valve_C5,disc_pump_power);
        analogWrite(pin_valve_C6,disc_pump_power);
        analogWrite(pin_valve_C7,disc_pump_power);
      }
    }
    flag_check_manual_inputs = false;

    /*
    // sensor measurement
    Wire1.requestFrom(SLF3x_ADDRESS, 3);
    signed_flow_value  = Wire1.read() << 8; // read the MSB from the sensor
    signed_flow_value |= Wire1.read();      // read the LSB from the sensor
    sensor_flow_crc    = Wire1.read();
    scaled_flow_value = ((float) signed_flow_value) / SCALE_FACTOR_FLOW;
    Serial.println(scaled_flow_value);
    */

    Wire1.requestFrom(SLF3x_ADDRESS, 9);
    if (Wire1.available() < 9)
    {
      Serial.println("I2C read error");
      return;
    }
    
    uint16_t sensor_flow_value  = Wire1.read() << 8; // read the MSB from the sensor
    sensor_flow_value |= Wire1.read();      // read the LSB from the sensor
    byte sensor_flow_crc    = Wire1.read();
    uint16_t sensor_temp_value  = Wire1.read() << 8; // read the MSB from the sensor
    sensor_temp_value |= Wire1.read();      // read the LSB from the sensor
    byte sensor_temp_crc    = Wire1.read();
    uint16_t aux_value          = Wire1.read() << 8; // read the MSB from the sensor
    aux_value         |= Wire1.read();      // read the LSB from the sensor
    byte aux_crc            = Wire1.read();
      
    int signed_temp_value = (int16_t) sensor_temp_value;
    float scaled_temp_value = ((float) signed_temp_value) / SCALE_FACTOR_TEMP;
    int signed_flow_value = (int16_t) sensor_flow_value;
    float scaled_flow_value = ((float) signed_flow_value) / SCALE_FACTOR_FLOW;
    
    Serial.print(scaled_temp_value);
    Serial.print('\t');
    Serial.println(scaled_flow_value);
    // Serial.println("test");
  }
}

void set_check_manual_input_flag()
{
  flag_check_manual_inputs = true;
}

void set_mode_to_vacuum()
{
  // set solenoid valve states
}

void set_mode_to_pressure()
{
  // set solenoid valve states
}

/************************************************
******************* disc pump *******************
************************************************/
bool write_disc_pump_command(char* cmd_str)
{
  int cmd_length = strlen(cmd_str);
  for(int i = 0;i<3;i++) // attempt 3 times
  {
    UART_disc_pump.clear(); // clear RX buffer
    UART_disc_pump.print(cmd_str);
    UART_disc_pump.flush(); // Wait for any transmitted data still in buffers to actually transmit
    delayMicroseconds(1000); // @@@ change to timeout-based appraoch
    disc_pump_rx_ptr = 0;
    while(UART_disc_pump.available())
      disc_pump_rx_buffer[disc_pump_rx_ptr++] = UART_disc_pump.read();
    if( cmd_length == disc_pump_rx_ptr && strncmp(cmd_str,disc_pump_rx_buffer,disc_pump_rx_ptr) == 0 )
      return true;
  }
  return false; // not receiving the sent command within 1 ms for 3 attempts
}

bool set_disc_pump_enabled(bool enabled)
{
  char cmd_str[32];
  sprintf(cmd_str,"#W0,%d\n",enabled);
  return write_disc_pump_command(cmd_str);
}

bool set_disc_pump_power(float power)
{
  char cmd_str[32];
  sprintf(cmd_str,"#W23,%f\n",power);
  UART_disc_pump.print(cmd_str);
}

void select_sensor_2()
{
  digitalWrite(pin_sensor_select,HIGH);
}

void select_sensor_1()
{
  digitalWrite(pin_sensor_select,LOW);
}
