Ports_Name = ['1','2','3','4','Air (5)','DAPI (6)','Nissl (7)','Wash Buffer (8)','Imaging Buffer (9)','Strip Buffer (10)']
Ports_Number = 	[1,2,3,4,5,6,7,8,9,10]

INCUBATION_TIME_MAX_MIN = 3600*3/60
FLOW_TIME_MAX = 60

SEQUENCE_ATTRIBUTES_KEYS = ['Sequence','Fluidic Port','Flow Time (s)','Incubation Time (min)','Repeat','Include']
SEQUENCE_NAME = ['Strip','Wash (Post-Strip)','Ligate','Stain with DAPI','Wash (Post-Ligation)','Add Imaging Buffer','Remove Medium']

# TIMER_CHECK_MCU_STATE_INTERVAL_MS = 10
TIMER_CHECK_MCU_STATE_INTERVAL_MS = 500 # for simulation
TIMER_CHECK_SEQUENCE_EXECUTION_STATE_INTERVAL_MS = 50

# MCU
MCU_CMD_LENGTH = 15
MCU_MSG_LENGTH = 20

# MCU - COMPUTER
T_DIFF_COMPUTER_MCU_MISMATCH_FAULT_THRESHOLD_SECONDS = 3

class SUBSEQUENCE_TYPE:
	MCU_CMD = 'MCU CMD'
	COMPUTER_STOPWATCH = 'COMPUTER STOPWATCH'

PRINT_DEBUG_INFO = True

# status of command execution on the MCU
class CMD_EXECUTION_STATUS:
	COMPLETED_WITHOUT_ERRORS = 0
	IN_PROGRESS = 1
	CMD_CHECKSUM_ERROR = 2
	CMD_INVALID = 3
	CMD_EXECUTION_ERROR = 4

#########################################################
############   Computer -> MCU command set   ############
#########################################################
class CMD_SET:
	CLEAR = 0
	REMOVE_MEDIUM = 1
	ADD_MEDIUM = 2

class CMD_SET_DESCRIPTION:
	CLEAR = 'Clear'
	REMOVE_MEDIUM = 'Remove Medium'
	ADD_MEDIUM = 'Add Medium'

class MCU_CMD_PARAMETERS:
	CONSTANT_POWER = 0
	CONSTANT_PRESSURE = 1
	CONSTANT_FLOW = 2
	VOLUME_CONTROL = 3

class MCU_CMD_PARAMETERS_DESCRIPTION:
	CONSTANT_POWER = 'constant power'
	CONSTANT_PRESSURE = 'constant pressure'
	CONSTANT_FLOW = 'constant flow'
	VOLUME_CONTROL = 'volume control'

class MCU_CONSTANTS:
	# pressure sensor HSCMRNN030PD2A3(x) HSCMRND030PD3A3(yes)
	_output_min = 1638; # 10% of 2^14
	_output_max = 14745; # 90% of 2^14
	_p_min = -30; # psi
	_p_max = 30; # psi

# status of internal program execution on the MCU

'''

#########################################################
#########   MCU -> Computer message structure   #########
#########################################################
byte 0-1	: computer -> MCU CMD counter (UID)
byte 2  	: cmd from host computer (error checking through check sum => no need to transmit back the parameters associated with the command)
		  	<see below for command set>
byte 3  	: status of the command
				- 1: in progress
				- 0: completed without errors
				- 2: error in cmd check sum
				- 3: invalid cmd
				- 4: error during execution
byte 4  	: MCU internal program being executed
				- 0: idle
			  	<see below for command set>
byte 5  	: state of valve A1,A2,B1,B2,bubble_sensor_1,bubble_sensor_2,x,x
byte 6  	: state of valve C1-C7, manual input bit
byte 7-8	: state of valve D1-D16
byte 9		: state of selector valve
byte 10-11	: pump power
byte 12-13	: pressure sensor 1 reading
byte 13-15	: pressure sensor 2 reading
byte 16-17	: flow sensor 1 reading
byte 18-19	: flow sensor 2 reading
byte 20-24	: reserved

#########################################################
#########   Computer -> MCU command structure   #########
#########################################################
byte 0-1	: computer -> MCU CMD counter
byte 2		: cmd from host computer
byte 3		: payload 1 (1 byte) - e.g. control type [constant power, constant pressure, constant flow, volume]
byte 4		: payload 2 (1 byte) - e.g. fluidic port
byte 5-6	: payload 3 (2 byte) - e.g. power, pressure, flow rate or volume setting
byte 7-10	: payload 4 (4 byte) - e.g. duration in ms
byte 11-14	: reserved (4 byte) (including checksum)

'''


# sequences
'''
1. strip - volume (time) [1.2 ml] - wait time - number of times [2]
2. wash (post-strip) - volume (time) [1.2 ml] - wait time - number of cycles [3]
3. sequencing mixture - all available - wait time
4. wash (post ligation) - volume (time) - wait time - number of cycles [3]
4. imaging buffer - volume (time) [1.2 ml]
5. DAPI - volume (time) [1.2 ml] - wait time
'''
