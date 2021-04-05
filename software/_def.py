NUMBER_OF_ROUNDS = 6

# for 1 ml syringe
class PUMP:
	STEPS_PER_UL = 384.00
	STEPS_MAX = 384000
	FOUR_STEPS_PER_SECOND_FACTOR = 1/0.625
	BACK_OFF_PARAMETER = 2465
	BACKLASH_PARAMETER = 0
	MEDIUM_BLEACH = 'B'
	MEDIUM_AIR = 'A'
	TARGET_BLEACH = 'B'
	TARGET_WASTE = 'W'
	DIRECTION_PULL = 'L'
	DIRECTION_PUSH = 'H'
	VOLUME_UL_MAX = 1000
	WITH_WAIT = 'W'
	WITHOUT_WAIT = 'N'

class BYPASS:
	TRUE = 'P'
	FALSE = 'F'

class LIGATION:
	PORTS = [5,6,7,8,9,10]
	FLOW_RATE_UL_PER_SECOND = 1.67
	FLOW_TIME_MIN = 5
	INCUBATION_TIME_MIN = 180
	FLOW_VOLUME_UL = 500

class WASH_PREIMAGING:
	PORT = 12
	FLOW_RATE_UL_PER_SECOND = 1.25
	FLOW_TIME_MIN = 20
	FLOW_VOLUME_UL = 1500

class IMAGING_BUFFER:
	PORT = 13
	FLOW_RATE_UL_PER_SECOND = 0.33
	FLOW_TIME_MIN = 20
	FLOW_VOLUME_UL = 400

class STRIP:
	PORT = 14
	FLOW_RATE_UL_PER_SECOND = 1.67
	FLOW_TIME_MIN = 10
	FLOW_VOLUME_UL = 1000

class WASH:
	PORT = 12
	PREFILL_VOLUME = 600 # for sample mounting prep, use a section of tubing in place of the flow cell
	PREFILL_SPEED = 35    # for sample mounting prep, use a section of tubing in place of the flow cell

class WASH_POSTIMAGING:
	PORT = 12
	FLOW_RATE_UL_PER_SECOND = 0.83
	FLOW_TIME_MIN = 30
	FLOW_VOLUME_UL = 1500

class BLEACH:
	FLOW_RATE_UL_PER_SECOND = 16.67
	FLOW_TIME_MIN = 5
	# FLOW_VOLUME_UL = 5000
	FLOW_VOLUME_UL = 2000
	PORT = 1

class NISSL:
	PORT = 2
	FLOW_RATE_UL_PER_SECOND = 1.67
	FLOW_TIME_MIN = 5
	FLOW_VOLUME_UL = 500
	IS_PRESENT = True

class DAPI:
	PORT = 3
	FLOW_RATE_UL_PER_SECOND = 1.67
	FLOW_TIME_MIN = 5
	FLOW_VOLUME_UL = 500
	IS_PRESENT = True

class PRIMING:
	FLOW_RATE_UL_PER_SECOND = 10

class RETURN:
	OK = 'ok\r\n'

class SERIAL:
	DELAY = 0.25