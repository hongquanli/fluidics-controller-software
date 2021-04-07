Ports_Name = ['1','2','3','4','Air (5)','DAPI (6)','Nissl (7)','Wash Buffer (8)','Imaging Buffer (9)','Strip Buffer (10)']
Ports_Number = 	[1,2,3,4,5,6,7,8,9,10]

INCUBATION_TIME_MAX_MIN = 3600*3/60
FLOW_TIME_MAX = 60

SEQUENCE_ATTRIBUTES_KEYS = ['Sequence','Fluidic Port','Flow Time (s)','Incubation Time (min)','Repeat','Include']
SEQUENCE_NAME = ['Strip','Wash (Post-Strip)','Ligate','Wash (Post-Ligation)','Add Imaging Buffer','Remove Imaging Buffer','Stain with DAPI']

# TIMER_CHECK_MCU_STATE_INTERVAL_MS = 10
TIMER_CHECK_MCU_STATE_INTERVAL_MS = 500 # for simulation

# MCU
MCU_CMD_LENGTH = 10
MCU_MSG_LENGTH = 20

# MCU - COMPUTER
T_DIFF_COMPUTER_MCU_MISMATCH_FAULT_THRESHOLD_SECONDS = 3


# computer to MCU cmd
C2M_CLEAR = 0

PRINT_DEBUG_INFO = True

# status of command execution on the MCU
class CMD_EXECUTION_STATUS:
	COMPLETED_WITHOUT_ERRORS = 0
	IN_PROGRESS = 1
	CMD_CHECKSUM_ERROR = 2
	CMD_INVALID = 3
	CMD_EXECUTION_ERROR = 4
# CMD_EXECUTION_STATUS.COMPLETED_WITHOUT_ERRORS = 0
# CMD_EXECUTION_STATUS.IN_PROGRESS = 1
# CMD_EXECUTION_STATUS.CMD_CHECKSUM_ERROR = 2
# CMD_EXECUTION_STATUS.CMD_INVALID = 3
# CMD_EXECUTION_STATUS.CMD_EXECUTION_ERROR = 4

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
byte 7-8	: pump power
byte 9-10	: pressure sensor 1 reading
byte 11-12	: pressure sensor 2 reading
byte 13-14	: flow sensor 1 reading
byte 15-16	: flow sensor 2 reading
byte 17-19	: reserved

#########################################################
#########   Computer -> MCU command structure   #########
#########################################################
byte 0-1	: computer -> MCU CMD counter
byte 2		: cmd from host computer
byte 3-4	: payload 1
byte 5-6	: payload 2
byte 7-9	: reserved (including checksum)



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
