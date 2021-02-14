static const int pin_manual_control_enable = 24;
static const int pin_pressure_vacuum = 25; 
static const int pin_analog_in = A12; // pin 26

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
  Timer_check_manual_input.begin(set_check_manual_input_flag,check_manual_input_interval_us);

  // disc pump serial
  Serial8.begin(115200);
  
}

void loop() {
  // put your main code here, to run repeatedly:

  if(flag_check_manual_inputs)
  {
    // check manual control
    flag_manual_control_enabled = digitalRead(pin_manual_control_enable);

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
      }
      else
      {
        disc_pump_power = 0;
        disc_pump_enabled = false;
        set_disc_pump_enabled(disc_pump_enabled);
        set_disc_pump_power(disc_pump_power);
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
  if(enabled==true)
  {
    char cmd[] = "#W0,1\n";
    return write_disc_pump_command(cmd);
  }
  else
  {
    char cmd[] = "#W0,0\n";
    return write_disc_pump_command(cmd);
  }
}

bool set_disc_pump_power(float power)
{
  char cmd_str[32];
  sprintf(cmd_str,"#W23,%f\n",power);
  UART_disc_pump.print(cmd_str);
}
