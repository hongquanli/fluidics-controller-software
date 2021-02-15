static const int pin_manual_control_enable = 24;
static const int pin_pressure_vacuum = 25; 
static const int pin_analog_in = A12; // pin 26

static const int pin_LED_error = 23;
static const int pin_LED_1 = 22;

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

void setup() 
{
  pinMode(pin_manual_control_enable, INPUT_PULLUP);
  pinMode(pin_pressure_vacuum, INPUT);
  
  pinMode(pin_LED_error, OUTPUT);
  pinMode(pin_LED_1, OUTPUT);

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
