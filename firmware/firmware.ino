#include <Wire.h>
#include <SPI.h>

//#define DEBUG_WITH_SERIAL true
#define DEBUG_WITH_SERIAL false
#define SELECTOR_VALVE_PRESENT true
// #define FLOW_SENSOR_2_PRESENT false

static const int pin_manual_control_enable = 24;
static const int pin_pressure_vacuum = 25;
static const int pin_analog_in = A12; // pin 26

static const int pin_LED_error = 23;
static const int pin_LED_1 = 22;

static const int pin_sensor_select = 15;

static const int pin_valve_A1 = 0;
static const int pin_valve_A2 = 1;
static const int pin_valve_B1 = 2;
static const int pin_valve_B2 = 3;

static const int pin_valve_C1 = 4;
static const int pin_valve_C2 = 5;
static const int pin_valve_C3 = 6;
static const int pin_valve_C4 = 7;
static const int pin_valve_C5 = 8;
static const int pin_valve_C6 = 9;
static const int pin_valve_C7 = 14;

static const int pin_33996_CS_0 = 10;
static const int pin_33996_PWM = 41;
static const int pin_33996_nRST = 40;

const int check_manual_input_interval_us = 5000; // 5 ms
const int read_sensors_interval_us = 5000; // 5 ms
const int send_update_interval_us = 20000; // 20 ms
IntervalTimer Timer_check_manual_input; // see https://www.pjrc.com/teensy/td_timing_IntervalTimer.html
IntervalTimer Timer_read_sensors_input;
IntervalTimer Timer_send_update_input;

volatile bool flag_check_manual_inputs = false;
volatile bool flag_read_sensors = false;
volatile bool flag_send_update = false;
bool flag_control_loop_update = true;

bool flag_manual_control_enabled = false; // based on hardware switch
int mode_pressure_vacuum = 0; // 0: pressure, 1: vacuum
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
const float SCALE_FACTOR_FLOW = 10.0; // Scale Factor for flow rate measurement, ul/min, SLF3S-0600F
//const float SCALE_FACTOR_FLOW = 500.0; // Scale Factor for flow rate measurement, ml/min, SLF3S-1300F
const float SCALE_FACTOR_TEMP = 200.0; // Scale Factor for temperature measurement
const char *UNIT_FLOW = " ml/min"; // physical unit of the flow rate measurement
const char *UNIT_TEMP = " deg C"; //physical unit of the temperature measurement
int ret;
int16_t signed_flow_value;
float scaled_flow_value;
byte sensor_flow_crc;
bool flow_sensor_present = false;
float volume_ul = 0;
float VOLUME_UL_MIN = 0;
static const float VOLUME_UL_MAX = 5000;

// IDEX selector valve
#define UART_Titan Serial5
int uart_titan_rx_ptr = 0;
char uart_titan_rx_buffer[32];

// 33996
uint16_t NXP33996_state = 0x0000;

// pressure sensor HSCMRNN030PD2A3(x) HSCMRND030PD3A3(yes)
const uint16_t _output_min = 1638; // 10% of 2^14
const uint16_t _output_max = 14745; // 90% of 2^14
const float _p_min = -30; // psi
const float _p_max = 30; // psi
float pressure_2 = 0; // pressure
float pressure_1 = 0; // vacuum
uint16_t pressure_2_raw = 0; 
uint16_t pressure_1_raw = 0;
uint16_t flow_2_raw = 0; // upstram
uint16_t flow_1_raw = 0; // downstream
bool flag_measure_volume = false;

// bubble sensor 
static const int pin_OCB350_0_calibrate = 29;
static const int pin_OCB350_0_B = 30;  // bubble sensor 1 - aspiration bubble sensor
static const int pin_OCB350_1_calibrate = 31;
static const int pin_OCB350_1_B = 32;
volatile bool liquid_present_1 = false;
volatile bool liquid_present_2 = false;

// communication with the python software
/*
#########################################################
#########   MCU -> Computer message structure   #########
#########################################################
byte 0-1  : computer -> MCU CMD counter (UID)
byte 2    : cmd from host computer (error checking through check sum => no need to transmit back the parameters associated with the command)
        <see below for command set>
byte 3    : status of the command
        - 1: in progress
        - 0: completed without errors
        - 2: error in cmd check sum
        - 3: invalid cmd
        - 4: error during execution
byte 4    : MCU internal program being executed
        - 0: idle
          <see below for command set>
byte 5    : state of valve A1,A2,B1,B2,bubble_sensor_1,bubble_sensor_2,x,x
byte 6    : state of valve C1-C7, manual input bit
byte 7-8  : state of valve D1-D16
byte 9    : state of selector valve
byte 10-11  : pump power
byte 12-13  : pressure sensor 1 reading (vacuum)
byte 14-15  : pressure sensor 2 reading (pressure)
byte 16-17  : flow sensor 1 reading (downstream)
byte 18-19  : flow sensor 2 reading (upstream)
byte 20     : elapsed time since the start of the last internal program (in seconds)
byte 21-22  : volume (ul), range: 0 - 5000
byte 23-24  : reserved
*/
static const int FROM_MCU_MSG_LENGTH = 25; // search for MCU_MSG_LENGTH in _def.py
static const int TO_MCU_CMD_LENGTH = 15; // search for MCU_CMD_LENGTH in _def.py
byte buffer_rx[1000];
byte buffer_tx[FROM_MCU_MSG_LENGTH];
volatile int buffer_rx_ptr;

// command sets - these are commands from the computer
// each of the commands may break down to multiple internal programs in the MCU
// search for class CMD_SET in _def.py
static const int CLEAR = 0;
static const int REMOVE_MEDIUM = 1;
static const int ADD_MEDIUM = 2;
static const int SET_SELECTOR_VALVE = 10;
static const int SET_10MM_SOLENOID_VALVE = 11;
static const int SET_SOLENOID_VALVE_B = 12;
static const int SET_SOLENOID_VALVE_C = 13;
static const int DISABLE_MANUAL_CONTROL = 20;
static const int ENABLE_PRESSURE_CONTROL_LOOP = 30;
static const int SET_PRESSURE_CONTROL_SETPOINT_PSI = 31;
static const int SET_PRESSURE_CONTROL_LOOP_P_COEFFICIENT = 32;
static const int SET_PRESSURE_CONTROL_LOOP_I_COEFFICIENT = 33;
//static const int SET_ASPIRATION_PUMP_POWER = 40;
//static const int SET_ASPIRATION_TIME_MS = 41;

// command parameters
// search for class MCU_CMD_PARAMETERS in _def.py
static const int CONSTANT_POWER = 0;
static const int CONSTANT_PRESSURE = 1;
static const int CONSTANT_FLOW = 2;
static const int VOLUME_CONTROL = 3;

// command execution status constants
// search for class CMD_EXECUTION_STATUS in _def.py
static const int COMPLETED_WITHOUT_ERRORS = 0;
static const int IN_PROGRESS = 1;
static const int CMD_CHECKSUM_ERROR = 2;
static const int CMD_INVALID = 3;
static const int CMD_EXECUTION_ERROR = 4;

// variables related to control by the software program
uint16_t current_command_uid = 0;
uint8_t current_command = 0;
uint8_t command_execution_status = IN_PROGRESS;
uint8_t internal_program = 0;
uint8_t selector_valve_position_setValue = 0;
bool manual_control_disabled_by_software = false;

// MCU internal program
static const int INTERNAL_PROGRAM_IDLE = 0;
static const int INTERNAL_PROGRAM_REMOVE_MEDIUM = 1;
static const int INTERNAL_PROGRAM_RAMP_UP_PRESSURE = 2;   // 2 -> 3 always
static const int INTERNAL_PROGRAM_PUMP_FLUID = 3;         // 3 -> 4 always 
static const int INTERNAL_PROGRAM_EMPTY_FLUIDIC_LINE = 4;
elapsedMillis elapsed_millis_since_remove_medium_started = 0;
elapsedMillis elapsed_millis_since_the_start_of_the_internal_program = 0; // for internal program 2-4
byte time_elapsed_s = 0;
unsigned long set_vacuum_duration_ms = 0;

bool pressure_control_loop_enabled = false;
int control_type = CONSTANT_POWER;
int fluidic_port = 0;
float control_setpoint = 0;
unsigned long set_flow_time_ms = 0;

// pressure control loop
float pressure_set_point = 0;
float pressure_loop_p_coefficient = 1;
float pressure_loop_i_coefficient = 1;
float pressure_loop_integral_error = 0;
float pressure_loop_error = 0;
static const float PRESSURE_FULL_SCALE_PSI = 5;

// default settings
//static const int DISC_PUMP_POWER_VACUUM = 960;
static const int VACUUM_DECAY_TIME_S = 1;
static const int PRESSURE_RAMP_UP_TIME_S = 5;
static const int DURATION_FOR_EMPTYING_THE_FLUIDIC_LINE_S = 5;
static const float PUMP_POWER_FOR_EMPTYING_THE_FLUIDIC_LINE = 0.4;
static const float PRESSURE_LOOP_COEFFICIENTS_FULL_SCALE = 100;

// fludic port setting
static const int PORT_AIR = 11;

/*************************************************************
 ************************** SETUP() **************************
 *************************************************************/

void setup()
{
  // USB serial
  Serial.begin(2000000);
  delayMicroseconds(5000);
  if (DEBUG_WITH_SERIAL)
    Serial.println("Connected"); // not showing up

  pinMode(pin_manual_control_enable, INPUT_PULLUP);
  pinMode(pin_pressure_vacuum, INPUT);

  pinMode(pin_LED_error, OUTPUT);
  pinMode(pin_LED_1, OUTPUT);

  pinMode(pin_sensor_select, OUTPUT);

  pinMode(pin_valve_A1, OUTPUT);
  pinMode(pin_valve_A2, OUTPUT);
  pinMode(pin_valve_B1, OUTPUT);
  pinMode(pin_valve_B2, OUTPUT);

  pinMode(pin_valve_C1, OUTPUT);
  pinMode(pin_valve_C2, OUTPUT);
  pinMode(pin_valve_C3, OUTPUT);
  pinMode(pin_valve_C4, OUTPUT);
  pinMode(pin_valve_C5, OUTPUT);
  pinMode(pin_valve_C6, OUTPUT);
  pinMode(pin_valve_C7, OUTPUT);

  analogWriteResolution(10);

  // bubble sensor
  pinMode(pin_OCB350_0_B, INPUT);
  pinMode(pin_OCB350_1_B, INPUT);

  // disc pump serial
  UART_disc_pump.begin(115200);
  UART_disc_pump.print("#W1,1000\n"); // limit pump power to 1000 mW
  UART_disc_pump.print("#W10,0\n");
  UART_disc_pump.print("#W11,0\n");

  // Titan selector valve serial
  UART_Titan.begin(19200);

  // I2C sensors
  Wire1.begin();

  // flow sensor
  int counter_tmp = 0;
  select_sensor_2();
  // Soft reset the sensor
  do {
    counter_tmp = counter_tmp + 1;
    Wire1.beginTransmission(0x00);
    Wire1.write(0x06);
    ret = Wire1.endTransmission();
    if (ret != 0) {
      if(DEBUG_WITH_SERIAL)
        Serial.println("Error while sending soft reset command, retrying...");
      delay(500); // wait long enough for chip reset to complete
    }
    if(counter_tmp == 5)
      break;
  } while (ret != 0);
  if(counter_tmp < 5)
    flow_sensor_present = true;

  if(flow_sensor_present)
  {
    // To perform a measurement, first send 0x3608 to switch to continuous
    do {
      Wire1.beginTransmission(SLF3x_ADDRESS);
      Wire1.write(0x36);
      Wire1.write(0x08);
      ret = Wire1.endTransmission();
      if (ret != 0) {
        if(DEBUG_WITH_SERIAL)
          Serial.println("Error starting measurement ...");
        delay(500); // wait long enough for chip reset to complete
      }
    } while (ret != 0);
  
    delay(100); // 60 ms needed for reliable measurements to begin
  }

  // 33996 and SPI
  pinMode(pin_33996_CS_0,OUTPUT);
  pinMode(pin_33996_PWM,OUTPUT);
  pinMode(pin_33996_nRST,OUTPUT);
  SPI.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV4);
  SPI.setDataMode(SPI_MODE1);
  SPI.setBitOrder(MSBFIRST);
  digitalWrite(pin_33996_nRST,HIGH);

  // test 33996
  for(int k = 0;k<1;k++)
  {
    for(int i=0;i<16;i++)
    {
      NXP33996_turn_on(i);
      NXP33996_update();
      delay(50);
      NXP33996_turn_off(i);
      NXP33996_update();
    }
  }  

  // test selector valve control
  /*
  if(SELECTOR_VALVE_PRESENT)
  {
    for(int i = 1;i<=12;i++)
    {
      // can remove
      if(DEBUG_WITH_SERIAL)
        Serial.println("----------------------------");
      selector_valve_position_setValue = i;
      set_selector_valve_position_blocking(selector_valve_position_setValue);
      check_selector_valve_position();
      uart_titan_rx_buffer[uart_titan_rx_ptr] = '\0'; // terminate the string
      // can remove
      if(DEBUG_WITH_SERIAL)
        Serial.println(uart_titan_rx_buffer);
    }
  }
  */
  
  // set up timers
  Timer_check_manual_input.begin(set_check_manual_input_flag, check_manual_input_interval_us);
  Timer_read_sensors_input.begin(set_read_sensors_flag, read_sensors_interval_us);
  Timer_send_update_input.begin(set_send_update_flag, send_update_interval_us);

  // NXP33996_turn_on(0);
  // NXP33996_update();

}

void loop() {

  /**************************************************************
   ********************** check serial input ********************
   **************************************************************/
  while(Serial.available())
  {
    buffer_rx[buffer_rx_ptr] = Serial.read();
    buffer_rx_ptr = buffer_rx_ptr + 1;
    if (buffer_rx_ptr == TO_MCU_CMD_LENGTH) 
    {
      buffer_rx_ptr = 0;
      current_command_uid = uint16_t(buffer_rx[0])*256 + uint16_t(buffer_rx[1]);
      current_command = buffer_rx[2];
      uint8_t payload1 = buffer_rx[3];
      uint8_t payload2 = buffer_rx[4];
      uint16_t payload3 = (uint16_t(buffer_rx[5])<<8) + uint16_t(buffer_rx[6]);
      uint32_t payload4 = (uint32_t(buffer_rx[7])<<24) + (uint32_t(buffer_rx[8])<<16) + (uint32_t(buffer_rx[9])<<8) + (uint32_t(buffer_rx[10]));

      // set the controller into appropreaite states based on the command received
      switch(current_command)
      {
        case CLEAR:
          current_command_uid = 0;
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;
          
        // diable/enable manual control
        case DISABLE_MANUAL_CONTROL:
          if(payload1==1)
            manual_control_disabled_by_software = true;
          if(payload1==0)
          {
            manual_control_disabled_by_software = false;
            pressure_control_loop_enabled = false; // may be changed in the future (e.g. use the knob to set pressure instead of power, right now pressure is set from the GUI)
          }
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;
          
        // remove medium
        case REMOVE_MEDIUM:
          manual_control_disabled_by_software = true;
          pressure_control_loop_enabled = false;
          digitalWrite(pin_valve_B1,LOW);
          set_vacuum_duration_ms = payload4;
          disc_pump_power = int((float(payload3)/65535)*1000);
          // disc_pump_power = DISC_PUMP_POWER_VACUUM;
          command_execution_status = IN_PROGRESS;
          internal_program = INTERNAL_PROGRAM_REMOVE_MEDIUM;
          set_mode_to_vacuum();
          disc_pump_enabled = true;
          set_disc_pump_enabled(disc_pump_enabled);
          set_disc_pump_power(disc_pump_power);
          elapsed_millis_since_remove_medium_started = 0;
          break;
          
        // add medium
        case ADD_MEDIUM:
          manual_control_disabled_by_software = true;
          command_execution_status = IN_PROGRESS;
          control_type = payload1;
          fluidic_port = payload2;
          control_setpoint = float(payload3)/65535;
          set_flow_time_ms = payload4;
          
          // enter the INTERNAL_PROGRAM_RAMP_UP_PRESSURE internal program
          internal_program = INTERNAL_PROGRAM_RAMP_UP_PRESSURE;
          // (0) close the valve between the selector valve and the chamber
          digitalWrite(pin_valve_B1,LOW);
          // (1) switch the fluidic port
          selector_valve_position_setValue = fluidic_port;
          set_selector_valve_position_blocking(selector_valve_position_setValue);
          check_selector_valve_position();
          uart_titan_rx_buffer[uart_titan_rx_ptr] = '\0'; // terminate the string
            // to add: convert the string to numeric value and compare it with selector_valve_position_setValue
            // to add: error handling
          // (2) turn on the 10 mm valve
          NXP33996_clear_all();
          NXP33996_turn_on(fluidic_port-1);
          NXP33996_update();
          // (3) start the control loop
          if(control_type==CONSTANT_PRESSURE)
          {
            pressure_set_point = control_setpoint*PRESSURE_FULL_SCALE_PSI;
            pressure_control_loop_enabled = true;
            pressure_loop_integral_error = 0;
            disc_pump_power = 0;
            set_disc_pump_power(disc_pump_power);
            disc_pump_enabled = true;
            set_disc_pump_enabled(disc_pump_enabled);
          }
          else if(control_type==CONSTANT_POWER)
          {
            set_mode_to_pressure();
            disc_pump_power = int(control_setpoint*1000);
            set_disc_pump_power(disc_pump_power);
            disc_pump_enabled = true;
            set_disc_pump_enabled(disc_pump_enabled);
          }
          // (4) start the timer
          elapsed_millis_since_the_start_of_the_internal_program = 0;          
          break;

        // set selector valve
        case SET_SELECTOR_VALVE:
          if(SELECTOR_VALVE_PRESENT)
          {
            selector_valve_position_setValue = payload2;
            set_selector_valve_position_blocking(selector_valve_position_setValue);
            check_selector_valve_position();
            uart_titan_rx_buffer[uart_titan_rx_ptr] = '\0'; // terminate the string
            // to add: convert the string to numeric value and compare it with selector_valve_position_setValue
            // to add: error handling
            command_execution_status = COMPLETED_WITHOUT_ERRORS;
          }
          break;
          
        // set 10 mm valve state
        case SET_10MM_SOLENOID_VALVE:
          if(payload2==0)
          {
            NXP33996_clear_all();
            NXP33996_update();
          }
          else
          {
            NXP33996_clear_all();
            NXP33996_turn_on(payload2-1);
            NXP33996_update();
          }
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;
          
        // set valve group B state
        case SET_SOLENOID_VALVE_B:
          if(payload1==0)
          {
            digitalWrite(pin_valve_B1,LOW);
            digitalWrite(pin_valve_B2,LOW);
          }
          if(payload1==1)
          {
            digitalWrite(pin_valve_B1,HIGH);
            digitalWrite(pin_valve_B2,LOW);
          }
          if(payload1==2)
          {
            digitalWrite(pin_valve_B1,LOW);
            digitalWrite(pin_valve_B2,HIGH);
          }
          if(payload1==3)
          {
            digitalWrite(pin_valve_B1,HIGH);
            digitalWrite(pin_valve_B2,HIGH);
          }
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;
          
        // set valve group C state
        case SET_SOLENOID_VALVE_C:
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;

        // pressure control loop
        case ENABLE_PRESSURE_CONTROL_LOOP:
          if(payload1==1)
          {
            manual_control_disabled_by_software = true;
            pressure_control_loop_enabled = true;
            pressure_loop_integral_error = 0;
            disc_pump_enabled = true;
            set_disc_pump_enabled(disc_pump_enabled);
          }
          if(payload1==0)
            pressure_control_loop_enabled = false;
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;

        // pressure p coefficient
        case SET_PRESSURE_CONTROL_LOOP_P_COEFFICIENT:
          pressure_loop_p_coefficient = (float(payload4)/4294967296)*PRESSURE_LOOP_COEFFICIENTS_FULL_SCALE;
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;

        // pressure i coefficient
        case SET_PRESSURE_CONTROL_LOOP_I_COEFFICIENT:
          pressure_loop_i_coefficient = (float(payload4)/4294967296)*PRESSURE_LOOP_COEFFICIENTS_FULL_SCALE;
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;
          
        // pressure set point
        case SET_PRESSURE_CONTROL_SETPOINT_PSI:
          pressure_set_point = (float(payload3)/65536)*PRESSURE_FULL_SCALE_PSI;
          command_execution_status = COMPLETED_WITHOUT_ERRORS;
          break;
      }
    }
  }

  /**************************************************************
   ********************** check manual input ********************
   **************************************************************/
  if (flag_check_manual_inputs)
  {
    // check manual control
    flag_manual_control_enabled = 1 - digitalRead(pin_manual_control_enable);

    // if manual input is enabled, check mode (pressure vs vacuum) and analog_in, set the pump power accordingly
    if (flag_manual_control_enabled)
    {

      // set mode (pressure vs vacuum)
      mode_pressure_vacuum = digitalRead(pin_pressure_vacuum); // GND - vacuum; VCC - pressure
      if (mode_pressure_vacuum == 1 )
        set_mode_to_vacuum();
      else
        set_mode_to_pressure();

      // set pump power
      analog_in = analogRead(pin_analog_in);
      if (analog_in > 23) // only enable the pump when the analog_in is > 23 (/1023)
      {
        disc_pump_power = analog_in - 23;
        disc_pump_enabled = true;
        set_disc_pump_power(disc_pump_power);
        set_disc_pump_enabled(disc_pump_enabled);
        analogWrite(pin_LED_1, disc_pump_power);
        //analogWrite(pin_valve_C1, disc_pump_power);
        //analogWrite(pin_valve_C2, disc_pump_power);
        analogWrite(pin_valve_C3, disc_pump_power);
        analogWrite(pin_valve_C4, disc_pump_power);
        analogWrite(pin_valve_C5, disc_pump_power);
        //analogWrite(pin_valve_C6, disc_pump_power);
        //analogWrite(pin_valve_C7, disc_pump_power);
      }
      else
      {
        // to be replaced with software control
        disc_pump_power = 0;
        disc_pump_enabled = false;
        set_disc_pump_enabled(disc_pump_enabled);
        set_disc_pump_power(disc_pump_power);
        analogWrite(pin_LED_1, disc_pump_power);
        //analogWrite(pin_valve_C1, disc_pump_power);
        //analogWrite(pin_valve_C2, disc_pump_power);
        analogWrite(pin_valve_C3, disc_pump_power);
        analogWrite(pin_valve_C4, disc_pump_power);
        analogWrite(pin_valve_C5, disc_pump_power);
        //analogWrite(pin_valve_C6, disc_pump_power);
        //analogWrite(pin_valve_C7, disc_pump_power);
      }
    }
    flag_check_manual_inputs = false;
  }

  /**************************************************************
   ************************* read sensors ***********************
   **************************************************************/
  if (flag_read_sensors)
  {
    flag_read_sensors = false;

    // flow sensor - disable for now
    if(flow_sensor_present)
    {
      select_sensor_2();
      /*
      Wire1.requestFrom(SLF3x_ADDRESS, 9);
      if (Wire1.available() < 9)
      {
        if(DEBUG_WITH_SERIAL)
          Serial.println("I2C read error");
        return;
      }
      uint16_t sensor_flow_value  = Wire1.read() << 8; // read the MSB from the sensor
      sensor_flow_value |= Wire1.read();      // read the LSB from the sensor
      flow_2_raw = sensor_flow_value;
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
      float scaled_flow_value = ((float) signed_flow_value) / SCALE_FACTOR_FLOW;*/
      Wire1.requestFrom(SLF3x_ADDRESS, 3);
      flow_2_raw  = Wire1.read() << 8; // read the MSB from the sensor
      flow_2_raw |= Wire1.read();      // read the LSB from the sensor
      sensor_flow_crc    = Wire1.read();
      int signed_flow_value = (int16_t) flow_2_raw;
      scaled_flow_value = ((float) signed_flow_value) / SCALE_FACTOR_FLOW;
      if(flag_measure_volume)
        volume_ul = volume_ul + scaled_flow_value*(read_sensors_interval_us/1000000.0/60.0);
    }
        
    // pressure sensor 2
    select_sensor_2();
    Wire1.requestFrom(0x38,2);
    if(Wire1.available() < 2)
    {
      if (DEBUG_WITH_SERIAL)
        Serial.println("pressure sensor 2 I2C read error");
      // clear buffer
      while(Wire1.available())
        Wire1.read();
      return;
    }
    uint8_t byte1 = Wire1.read();
    uint8_t byte2 = Wire1.read();
    uint8_t byte3 = Wire1.read();
    uint8_t byte4 = Wire1.read();
    byte _status = byte1 >> 6;
    uint16_t _bridge_data = (byte1 << 8 | byte2) & 0x3FFF;
    pressure_2_raw = _bridge_data;
    pressure_2 = float(constrain(_bridge_data, _output_min, _output_max) - _output_min) * (_p_max - _p_min) / (_output_max - _output_min) + _p_min;
    // uint16_t _temperature_raw = (byte3 << 3 | byte4 >> 5);
    // float temperature_2 = (float(_temperature_raw)/2047.0)*200 - 50;

    // pressure sensor 1
    select_sensor_1();
    Wire1.requestFrom(0x38,2);
    if(Wire1.available() < 2)
    {
      if (DEBUG_WITH_SERIAL)
        Serial.println("pressure sensor 1 I2C read error");
      // clear buffer
      while(Wire1.available())
        Wire1.read();
      return;
    }
    byte1 = Wire1.read();
    byte2 = Wire1.read();
    _status = byte1 >> 6;
    _bridge_data = (byte1 << 8 | byte2) & 0x3FFF;
    pressure_1_raw = _bridge_data;
    pressure_1 = float(constrain(_bridge_data, _output_min, _output_max) - _output_min) * (_p_max - _p_min) / (_output_max - _output_min) + _p_min;

    // bubble sensor
    liquid_present_1 = 1 - digitalRead(pin_OCB350_0_B);
    liquid_present_2 = 1 - digitalRead(pin_OCB350_1_B);

    flag_control_loop_update = true;
  }

  /*********************************************************
   ***************** pressure control loop *****************
   *********************************************************/
  if(flag_control_loop_update)
  {
    if(pressure_control_loop_enabled)
    {
      pressure_loop_error = pressure_set_point - pressure_2;
      pressure_loop_integral_error = pressure_loop_integral_error + pressure_loop_error;
      pressure_loop_integral_error = min(1/pressure_loop_i_coefficient,pressure_loop_integral_error);
      pressure_loop_integral_error = max(0,pressure_loop_integral_error);
      disc_pump_power = int((pressure_loop_integral_error*pressure_loop_i_coefficient+pressure_loop_error*pressure_loop_p_coefficient)*1000);
      disc_pump_power = min(1000,disc_pump_power);
      disc_pump_power = max(0,disc_pump_power);
      set_disc_pump_power(disc_pump_power);
    }
    flag_control_loop_update = false;
  }

  /*********************************************************
   ******************* state transition ********************
   *********************************************************/
   switch(internal_program)
   {
    // idle
    case INTERNAL_PROGRAM_IDLE:
      break;
      
    // remove medium
    case INTERNAL_PROGRAM_REMOVE_MEDIUM:
      time_elapsed_s = elapsed_millis_since_remove_medium_started/1000;
      // to add - bubble sensor integration
      if(elapsed_millis_since_remove_medium_started>set_vacuum_duration_ms)
      {
        disc_pump_power = 0;
        set_disc_pump_power(disc_pump_power);
        disc_pump_enabled = false;
        set_disc_pump_enabled(disc_pump_enabled);
        set_mode_to_pressure();
      }
      if(elapsed_millis_since_remove_medium_started>set_vacuum_duration_ms+1000*VACUUM_DECAY_TIME_S)
      {
        internal_program = INTERNAL_PROGRAM_IDLE;
        command_execution_status = COMPLETED_WITHOUT_ERRORS;
        time_elapsed_s = 0;
      }
      break;

    // ramp up pump power
    case INTERNAL_PROGRAM_RAMP_UP_PRESSURE:
      time_elapsed_s = elapsed_millis_since_the_start_of_the_internal_program/1000;
      if(elapsed_millis_since_the_start_of_the_internal_program>=PRESSURE_RAMP_UP_TIME_S*1000 || (control_type == CONSTANT_PRESSURE && pressure_2 >= pressure_set_point))
      {
        // enter the next phase
        // (1) open the valve between the selector valve and the chamber
        digitalWrite(pin_valve_B1,HIGH);
        // (2) get to the next phase
        internal_program = INTERNAL_PROGRAM_PUMP_FLUID;
        // (3) reset the timer
        elapsed_millis_since_the_start_of_the_internal_program = 0;
        // (4) reset the dispensed volume
        volume_ul = 0;
      }
      break;

    // pump fluid
    case INTERNAL_PROGRAM_PUMP_FLUID:
      flag_measure_volume = true;
      time_elapsed_s = elapsed_millis_since_the_start_of_the_internal_program/1000;
      if(elapsed_millis_since_the_start_of_the_internal_program>=set_flow_time_ms)
      {
        // (1) close the valve between the selector valve and the chamber
        digitalWrite(pin_valve_B1,LOW);
        // (2) stop the pump
        if(control_type==CONSTANT_PRESSURE)
        {
          pressure_set_point = 0;
          pressure_control_loop_enabled = false;
          pressure_loop_integral_error = 0;
        }
        disc_pump_power = 0;
        set_disc_pump_power(disc_pump_power);
        disc_pump_enabled = false;
        set_disc_pump_enabled(disc_pump_enabled);        
        // (3) release the pressure
        NXP33996_clear_all();
        NXP33996_update();
        // (4) switch to the air path
        selector_valve_position_setValue = PORT_AIR;
        set_selector_valve_position_blocking(selector_valve_position_setValue);
        check_selector_valve_position();
        uart_titan_rx_buffer[uart_titan_rx_ptr] = '\0'; // terminate the string
          // to add: convert the string to numeric value and compare it with selector_valve_position_setValue
          // to add: error handling
        NXP33996_turn_on(PORT_AIR-1);
        NXP33996_update();
        // (5) start pumping again
        if(control_type==CONSTANT_POWER)
        {
          // start the pump
          disc_pump_power = PUMP_POWER_FOR_EMPTYING_THE_FLUIDIC_LINE*1000;
          set_disc_pump_power(disc_pump_power);
          disc_pump_enabled = true;
          set_disc_pump_enabled(disc_pump_enabled);  
          // open the valve between the selector valve and the chamber
          digitalWrite(pin_valve_B1,HIGH);
        }
        else if(control_type==CONSTANT_PRESSURE)
        {
          // connect the fluidic path and re-enter the pressure loop
          digitalWrite(pin_valve_B1,HIGH);
          // enable the pressure loop again
          pressure_set_point = control_setpoint*PRESSURE_FULL_SCALE_PSI;
          pressure_control_loop_enabled = true;
          pressure_loop_integral_error = 0;
          disc_pump_power = 0;
          set_disc_pump_power(disc_pump_power);
          disc_pump_enabled = true;
          set_disc_pump_enabled(disc_pump_enabled);
        }
        // (6) reset the timer and go to the next phase
        internal_program = INTERNAL_PROGRAM_EMPTY_FLUIDIC_LINE;
        elapsed_millis_since_the_start_of_the_internal_program = 0;
      }
      break;
    case INTERNAL_PROGRAM_EMPTY_FLUIDIC_LINE:
      time_elapsed_s = elapsed_millis_since_the_start_of_the_internal_program/1000;
      if(elapsed_millis_since_the_start_of_the_internal_program>=1000*DURATION_FOR_EMPTYING_THE_FLUIDIC_LINE_S)
      {
        // stop the pressure loop if the control type is constant pressure
        if(control_type==CONSTANT_PRESSURE)
        {
          pressure_set_point = 0;
          pressure_control_loop_enabled = false;
          pressure_loop_integral_error = 0;
        }
        // stop the disc pump
        disc_pump_power = 0;
        set_disc_pump_power(disc_pump_power);
        disc_pump_enabled = false;
        set_disc_pump_enabled(disc_pump_enabled); 
        // turn off the solenoid valve
        NXP33996_clear_all();
        NXP33996_update();
        internal_program = INTERNAL_PROGRAM_IDLE;
        command_execution_status = COMPLETED_WITHOUT_ERRORS;
        time_elapsed_s = 0;
        // close the valve between the selector valve and the chamber
        digitalWrite(pin_valve_B1,LOW);
        flag_measure_volume = false;
      }
      break;
   }

  /*********************************************************
   ********************** send update **********************
   *********************************************************/
  if(flag_send_update)
  {
    if(DEBUG_WITH_SERIAL)
    {
      // Serial.print(scaled_temp_value);
      // Serial.print('\t');
      Serial.print(scaled_flow_value);
      Serial.print("\t pressure (psi): ");
      Serial.print(pressure_2);
      Serial.print("\t vacuum (psi): ");
      Serial.print(pressure_1);
      Serial.print("\t upstream bubble sensor: ");
      // Serial.print("pin_OCB350_0_B: ");
      Serial.print(digitalRead(pin_OCB350_1_B));
      Serial.print("\t downstream bubble sensor: ");
      // Serial.print("pin_OCB350_1_B: ");
      Serial.println(digitalRead(pin_OCB350_0_B));
    }
    else
    {
      /*
      byte 0-1  : computer -> MCU CMD counter (UID)
      byte 2    : cmd from host computer (error checking through check sum => no need to transmit back the parameters associated with the command)
              <see below for command set>
      byte 3    : status of the command
              - 1: in progress
              - 0: completed without errors
              - 2: error in cmd check sum
              - 3: invalid cmd
              - 4: error during execution
      byte 4    : MCU internal program being executed
              - 0: idle
                <see below for command set>
      byte 5    : state of valve A1,A2,B1,B2,bubble_sensor_1,bubble_sensor_2,x,x
      byte 6    : state of valve C1-C7, manual input bit
      byte 7-8  : state of valve D1-D16
      byte 9    : state of selector valve
      byte 10-11  : pump power
      byte 12-13  : pressure sensor 1 reading (vacuum)
      byte 14-15  : pressure sensor 2 reading (pressure)
      byte 16-17  : flow sensor 1 reading (downstram)
      byte 18-19  : flow sensor 2 reading (upstram)
      byte 20     : elapsed time since the start of the last internal program (in seconds)
      byte 21-22  : volume (ul), range: 0 - 5000
      byte 23-24  : reserved
      */
      buffer_tx[0] = byte(current_command_uid >> 8);
      buffer_tx[1] = byte(current_command_uid % 256);
      buffer_tx[2] = current_command;
      buffer_tx[3] = command_execution_status;
      buffer_tx[4] = internal_program;
      buffer_tx[5] = 0; // to finish
      buffer_tx[5] = buffer_tx[5] | (liquid_present_1 << 3);
      buffer_tx[5] = buffer_tx[5] | (liquid_present_2 << 2);
      buffer_tx[6] = 0; // to do
      buffer_tx[7] = byte(NXP33996_state >> 8);
      buffer_tx[8] = byte(NXP33996_state % 256);
      buffer_tx[9] = byte(selector_valve_position_setValue);
      buffer_tx[10] = byte(int(disc_pump_power/1000*65535) >> 8);
      buffer_tx[11] = byte(int(disc_pump_power/1000*65535) % 256);
      buffer_tx[12] = byte(pressure_1_raw >> 8); // vacuum
      buffer_tx[13] = byte(pressure_1_raw % 256 ); // vacuum
      buffer_tx[14] = byte(pressure_2_raw >> 8); // pressure
      buffer_tx[15] = byte(pressure_2_raw % 256 ); // vacuum
      buffer_tx[16] = byte(flow_1_raw >> 8); // pressure
      buffer_tx[17] = byte(flow_1_raw % 256 ); // vacuum
      buffer_tx[18] = byte(flow_2_raw >> 8); // pressure
      buffer_tx[19] = byte(flow_2_raw % 256 ); // vacuum
      buffer_tx[20] = byte(time_elapsed_s);
      uint16_t volume_ul_uint16 = (volume_ul/VOLUME_UL_MAX)*65535;
      buffer_tx[21] = byte(volume_ul_uint16 >> 8);
      buffer_tx[22] = byte(volume_ul_uint16 % 256);
      SerialUSB.write(buffer_tx,FROM_MCU_MSG_LENGTH);  
    }
    flag_send_update = false;
  }
}

/************************************************
************* flag setting functions ************
************************************************/

void set_check_manual_input_flag()
{
  if(manual_control_disabled_by_software==false)
    flag_check_manual_inputs = true;
}

void set_read_sensors_flag()
{
  flag_read_sensors = true;
}

void set_send_update_flag()
{
  flag_send_update = true;
  if(DEBUG_WITH_SERIAL)
    Serial.println("flag_send_update = true");
}

/************************************************
******************** valving ********************
************************************************/

void set_mode_to_vacuum()
{
  // set solenoid valve states
  digitalWrite(pin_valve_A1,HIGH);
  digitalWrite(pin_valve_A2,HIGH);
  
  //  // for testing only, to be removed
  //  selector_valve_position_setValue = 2;
  //  set_selector_valve_position_blocking(selector_valve_position_setValue);
}

void set_mode_to_pressure()
{
  // set solenoid valve states
  // digitalWrite(pin_valve_B1,LOW); // to prevent any flow until explictly opening the valve after the selector valve output
  digitalWrite(pin_valve_A1,LOW);
  digitalWrite(pin_valve_A2,LOW);

  //  // for testing only, to be removed
  //  selector_valve_position_setValue = 1;
  //  set_selector_valve_position_blocking(selector_valve_position_setValue);
}

/************************************************
******************* disc pump *******************
************************************************/
bool write_disc_pump_command(char* cmd_str)
{
  int cmd_length = strlen(cmd_str);
  for (int i = 0; i < 3; i++) // attempt 3 times
  {
    UART_disc_pump.clear(); // clear RX buffer
    UART_disc_pump.print(cmd_str);
    UART_disc_pump.flush(); // Wait for any transmitted data still in buffers to actually transmit
    delayMicroseconds(1000); // @@@ change to timeout-based appraoch
    disc_pump_rx_ptr = 0;
    while (UART_disc_pump.available())
      disc_pump_rx_buffer[disc_pump_rx_ptr++] = UART_disc_pump.read();
    if ( cmd_length == disc_pump_rx_ptr && strncmp(cmd_str, disc_pump_rx_buffer, disc_pump_rx_ptr) == 0 )
      return true;
  }
  return false; // not receiving the sent command within 1 ms for 3 attempts
}

bool set_disc_pump_enabled(bool enabled)
{
  char cmd_str[32];
  sprintf(cmd_str, "#W0,%d\n", enabled);
  return write_disc_pump_command(cmd_str);
}

bool set_disc_pump_power(float power)
{
  char cmd_str[32];
  sprintf(cmd_str, "#W23,%f\n", power);
  // UART_disc_pump.print(cmd_str);
  return write_disc_pump_command(cmd_str);
}

void select_sensor_2()
{
  digitalWrite(pin_sensor_select, HIGH);
}

void select_sensor_1()
{
  digitalWrite(pin_sensor_select, LOW);
}

bool write_selector_valve_read_command(char* cmd_str)
{
  for (int i = 0; i < 3; i++) // attempt 3 times
  {
    // empty the UART buffer
    while (UART_Titan.available())
      UART_Titan.read();

    UART_Titan.print(cmd_str);
    UART_Titan.flush(); // Wait for any transmitted data still in buffers to actually transmit
    elapsedMillis time_elapsed_ms;
    uart_titan_rx_ptr = 0;
    while (time_elapsed_ms < 5) // timeout after 5ms
    {
      while (UART_Titan.available())
        uart_titan_rx_buffer[uart_titan_rx_ptr++] = UART_Titan.read();
      if (uart_titan_rx_ptr > 0 && uart_titan_rx_buffer[uart_titan_rx_ptr - 1] == '\r')
        return true;
    }
  }
  if (DEBUG_WITH_SERIAL)
    Serial.println("> 2 failed attempts");
  return false;
}

bool write_selector_valve_move_command(char* cmd_str)
{
  for (int i = 0; i < 2; i++) // attempt 2 times
  {
    /*
      if(DEBUG_WITH_SERIAL)
      {
        Serial.print("> sending ");
        Serial.println(cmd_str);
      }
    */

    // empty the UART buffer
    while (UART_Titan.available())
      UART_Titan.read();

    UART_Titan.print(cmd_str);
    UART_Titan.flush(); // Wait for any transmitted data still in buffers to actually transmit
    elapsedMillis time_elapsed_ms;
    uart_titan_rx_ptr = 0;
    while ( time_elapsed_ms < 5000) // timeout after 5 second if the '/r' is not returned
    {
      while (UART_Titan.available())
        uart_titan_rx_buffer[uart_titan_rx_ptr++] = UART_Titan.read();
      if (uart_titan_rx_ptr > 0 && uart_titan_rx_buffer[uart_titan_rx_ptr - 1] == '\r') // can change to just read up to one byte
        return true;
    }
  }
  if (DEBUG_WITH_SERIAL)
    Serial.println("> 2 failed attempts");
  return false;
}

bool set_selector_valve_position(int pos)
{
  char cmd_str[32];
  sprintf(cmd_str, "P%02X\r", pos);
  return write_selector_valve_move_command(cmd_str);
}

bool check_selector_valve_position()
{
  // During the valve motion profile, driver board will not accept any commands
  // and will respond to any incoming data with ‘*’ [0x2A].
  char cmd_str[32];
  sprintf(cmd_str, "S\r");
  return write_selector_valve_read_command(cmd_str);
  // false will be returned during motion (the command will be sent three times and '*' will be returned)
  // when true is returned, the valve position is in the rx buffer
}

bool set_selector_valve_position_blocking(int pos)
{
  bool command_sent = set_selector_valve_position(pos);
  if (command_sent == false)
    if (DEBUG_WITH_SERIAL)
      Serial.println("> UART write command failed");
  return false; // in the future can return an error code

  while (check_selector_valve_position() == false)
  {
    if (DEBUG_WITH_SERIAL)
      Serial.println("> valve in motion");
  }
  // to do: add timeout

  if (DEBUG_WITH_SERIAL)
    Serial.println("> exit the blocking call");

  return true;
}

void NXP33996_clear_all()
{
  NXP33996_state = (uint16_t)0x0000;
}

void NXP33996_turn_on(int id)
{
  NXP33996_state |= (uint16_t)0x0001 << id;
}

void NXP33996_turn_off(int id)
{
  NXP33996_state &= ~((uint16_t)0x0001 << id);
}

void NXP33996_update()
{
  digitalWrite(pin_33996_CS_0,LOW);
  SPI.transfer(0x00);
  SPI.transfer16(NXP33996_state); //16 output bits
  digitalWrite(pin_33996_CS_0,HIGH);
}
