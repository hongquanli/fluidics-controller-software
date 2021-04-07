# set QT_API environment variable
import os 
os.environ["QT_API"] = "pyqt5"
import qtpy

# qt libraries
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

# other libraries
import utils
import platform
import serial
import serial.tools.list_ports
import io
import sys
import time
import queue
from pathlib import Path

from _def import *

'''
trigger control
'''

INTERVAL_SCANNING_TRIGGER_IN_ms = 50
BYTE_SEND_TRIGGER = 'T'.encode()
BYTE_TRIGGER_RECEIVED = 'T'.encode()

class trigger_controller_arduino(object):
	def __init__(self):
		# locate serial port
		arduino_ports = [
				p.device
				for p in serial.tools.list_ports.comports()
				if 'Arduino' in p.description]
		if not arduino_ports:
			raise IOError("No Arduino found")
		if len(arduino_ports) > 1:
			warnings.warn('Multiple Arduinos found - using the first')
			print('Using Arduino found at : {}'.format(arduino_ports[0]))			
		# establish serial communication
		self.serial = serial.Serial(arduino_ports[0],2000000)
		utils.print_message('Trigger Controller Connected')
		time.sleep(0.2)
	
	def __del__(self):
		self.serial.close()

	def send_trigger(self):
		self.serial.write(BYTE_SEND_TRIGGER)

class TriggerController(QObject):

	triggerReceived = Signal()
	log_message = Signal(str)

	def __init__(self):
		QObject.__init__(self)
		self.microcontroller = trigger_controller_arduino()
		self.timer_listening_for_trigger_in = QTimer()
		self.timer_listening_for_trigger_in.setInterval(INTERVAL_SCANNING_TRIGGER_IN_ms)
		self.timer_listening_for_trigger_in.timeout.connect(self.scan_trigger_in)
		self.timer_listening_for_trigger_in.start()
		self.trigger_received = False

	def send_trigger(self):
		self.microcontroller.send_trigger()
		self.log_message.emit(utils.timestamp() + 'Microscope Trigger Sent')
		QApplication.processEvents()

	def scan_trigger_in(self):
		if self.microcontroller.serial.in_waiting==0:
			return
		byte_received = self.microcontroller.serial.read()
		if byte_received == BYTE_TRIGGER_RECEIVED:
			self.trigger_received = True
			self.triggerReceived.emit()
			self.log_message.emit(utils.timestamp() + 'Trigger Received - Imaging Completed')
			QApplication.processEvents()

class TriggerController_simulation(QObject):

	triggerReceived = Signal()
	log_message = Signal(str)

	def __init__(self):
		QObject.__init__(self)
		self.timer_listening_for_trigger_in = QTimer()
		self.timer_listening_for_trigger_in.setInterval(3000)
		self.timer_listening_for_trigger_in.timeout.connect(self.scan_trigger_in)
		# self.timer_listening_for_trigger_in.start()
		self.trigger_received = False

	def send_trigger(self):
		self.log_message.emit(utils.timestamp() + 'Microscope Trigger Sent')
		QApplication.processEvents()

	def scan_trigger_in(self):
		self.trigger_received = True
		self.triggerReceived.emit()
		self.log_message.emit(utils.timestamp() + 'Trigger Received - Imaging Completed')
		QApplication.processEvents()

'''
fluid control
'''

class Microcontroller(object):
	def __init__(self):
		self.serial = None
		self.tx_buffer_length = MCU_CMD_LENGTH
		self.rx_buffer_length = MCU_MSG_LENGTH

		controller_ports = [
				p.device
				for p in serial.tools.list_ports.comports()
				#if 'USB-Serial Controller D' in p.description] # for Mac
				if 'Prolific' in p.description] # for windows
		if not controller_ports:
			raise IOError("No Controller Found")
		self.serial = serial.Serial(controller_ports[0],2000000)
		utils.print_message('Fluid Controller Connected')
		# clear counter - @@@ to add

	def __del__(self):
		self.serial.close()

	def read_received_packet_nowait(self):
		# wait to receive data
		if self.serial.in_waiting==0:
			return None
		if self.serial.in_waiting % self.rx_buffer_length != 0:
			return None
		
		# get rid of old data
		num_bytes_in_rx_buffer = self.serial.in_waiting
		if num_bytes_in_rx_buffer > self.rx_buffer_length:
			# print('getting rid of old data')
			for i in range(num_bytes_in_rx_buffer-self.rx_buffer_length):
				self.serial.read()

		# read the buffer
		data=[]
		for i in range(self.rx_buffer_length):
			data.append(ord(self.serial.read()))
		return data

	def send_command(self,cmd):
		self.serial.write(cmd)

class Microcontroller_Simulation(object):
	def __init__(self):
		self.serial = None
		self.tx_buffer_length = MCU_CMD_LENGTH
		self.rx_buffer_length = MCU_MSG_LENGTH
		utils.print_message('MCU simulator connected')		

		# for simulation 
		self.timer_update_command_execution_status = QTimer()
		self.timer_update_command_execution_status.timeout.connect(self._update_cmd_execution_status)
		self.cmd_execution_status = 0
		self.current_cmd = 0
		self.current_cmd_uid = 0
	
	def __del__(self):
		pass

	def read_received_packet_nowait(self):
		msg=[]
		for i in range(self.rx_buffer_length):
			msg.append(0)
		msg[0] = self.current_cmd_uid >> 8
		msg[1] = self.current_cmd_uid & 0xff
		msg[2] = self.current_cmd
		msg[3] = self.cmd_execution_status
		# if PRINT_DEBUG_INFO:
		# 	print('### msg from the MCU: ' + str(msg) + ']')
		return msg

	def send_command(self,cmd):
		self.current_cmd_uid = (cmd[0] << 8) + cmd[1]
		self.current_cmd = cmd[2]
		self.cmd_execution_status = CMD_EXECUTION_STATUS.IN_PROGRESS
		self.timer_update_command_execution_status.setInterval(2000)
		self.timer_update_command_execution_status.start()
		if PRINT_DEBUG_INFO:
			print('### cmd sent to mcu: ' + str(cmd))
			print('[MCU currend cmd uid is ' + str(self.current_cmd_uid) + ' ]')

	def _update_cmd_execution_status(self):
		print('simulation - MCU command execution finished')
		self.cmd_execution_status = CMD_EXECUTION_STATUS.COMPLETED_WITHOUT_ERRORS
		# print('simulation - MCU command execution error')
		# self.cmd_execution_status = CMD_EXECUTION_STATUS.CMD_EXECUTION_ERROR
		self.timer_update_command_execution_status.stop()

###################################################
################# FluidController #################
###################################################
class Sequence():
	def __init__(self,sequence_name,fluidic_port,flow_time_s,incubation_time_min,pressure_setting=None,round_=1):
		self.sequence_name = sequence_name
		self.fluidic_port = fluidic_port
		self.flow_time_s = flow_time_s
		self.incubation_time_min = incubation_time_min
		self.pressure_setting = pressure_setting
		self.round = round_

		self.sequence_started = False
		self.queue_subsequences = queue.Queue()

		# populate the queue of subsequences, depending on the tyepes of the sequence
		# case 1: strip, wash (post-strip), ligate, wash (post-ligate)
		# case 2: add imaging buffer, (stain with DAPI)
		# case 3: remove imaging buffer (can apply to removing any other liquid)

		'''
		if flow_time <= 0: # case 3, remove liquid
			pass
		'''

		if True:
			# subsequence 0
			mcu_command = Microcontroller_Command(1,1,1)
			self.queue_subsequences.put(Subsequence(SUBSEQUENCE_TYPE.MCU_CMD,mcu_command))

			# subsequence 1
			mcu_command = Microcontroller_Command(2,2,2)
			self.queue_subsequences.put(Subsequence(SUBSEQUENCE_TYPE.MCU_CMD,mcu_command))

			# subsequence 2
			mcu_command = Microcontroller_Command(3,3,3)
			self.queue_subsequences.put(Subsequence(SUBSEQUENCE_TYPE.MCU_CMD,mcu_command))

			# subsequence 3
			mcu_command = Microcontroller_Command(1,1,1)
			self.queue_subsequences.put(Subsequence(SUBSEQUENCE_TYPE.COMPUTER_STOPWATCH,microcontroller_command=None,stopwatch_time_remaining_seconds=5))


class Subsequence():
	def __init__(self,subsequence_type=None,microcontroller_command=None,stopwatch_time_remaining_seconds=None):
		self.subsequence_type = subsequence_type
		self.cmd = microcontroller_command
		self.stopwatch_time_remaining_seconds = stopwatch_time_remaining_seconds

class Microcontroller_Command():
	def __init__(self,cmd,payload1=0,payload2=0):
		self.cmd = cmd
		self.payload1 = payload1
		self.payload2 = payload2

	def get_ready_to_decorate_cmd_packet(self):
		return self._format_command()

	def _format_command(self):
		cmd_packet = bytearray(MCU_CMD_LENGTH)
		cmd_packet[0] = 0 # reserved byte for UID
		cmd_packet[1] = 0 # reserved byte for UID
		cmd_packet[2] = self.cmd
		cmd_packet[3] = self.payload1 >> 8
		cmd_packet[4] = self.payload1 & 0xff
		cmd_packet[5] = self.payload2 >> 8
		cmd_packet[6] = self.payload2 & 0xff
		return cmd_packet

class FluidController(QObject):
	
	log_message = Signal(str)

	def __init__(self,microcontroller):
		QObject.__init__(self)
		self.microcontroller = microcontroller		
		self.cmd_length = MCU_CMD_LENGTH

		# clear counter on both the computer and the MCU
		self.computer_to_MCU_command_counter = 0 # this is the UID
		self.computer_to_MCU_command = C2M_CLEAR # when init the MCU in the firmware, set computer_to_MCU_command = 255 (reserved), so that there will be mismatch until proper communication
		mcu_cmd = Microcontroller_Command(self.computer_to_MCU_command)
		cmd_packet = mcu_cmd.get_ready_to_decorate_cmd_packet()
		cmd_packet = self._add_UID_to_mcu_command_packet(cmd_packet,self.computer_to_MCU_command_counter)
		self.microcontroller.send_command(cmd_packet)

		self.abort_sequences_requested = False
		self.sequences_in_progress = False
		self.current_sequence = None

		self.queue_sequence = queue.Queue()
		self.queue_subsequence = queue.Queue()
		self.queque_to_Microcontroller_Command = queue.Queue()

		self.timer_check_microcontroller_state = QTimer()
		self.timer_check_microcontroller_state.setInterval(TIMER_CHECK_MCU_STATE_INTERVAL_MS)
		self.timer_check_microcontroller_state.timeout.connect(self._check_microcontroller_state)
		self.timer_check_microcontroller_state.start()

		self.timer_update_sequence_execution_state = QTimer()
		self.timer_update_sequence_execution_state.setInterval(TIMER_CHECK_SEQUENCE_EXECUTION_STATE_INTERVAL_MS)
		self.timer_update_sequence_execution_state.timeout.connect(self._update_sequence_execution_state)
		self.timer_update_sequence_execution_state.start()

		self.timestamp_last_computer_mcu_mismatch = None

	def _add_UID_to_mcu_command_packet(self,cmd,command_UID):
		cmd[0] = command_UID >> 8
		cmd[1] = command_UID & 0xff
		return cmd

	def _update_sequence_execution_state(self):
		if self.sequences_in_progress:
			if self.current_sequence == None:
				# if the queue is not empty, load the next sequence to execute
				if self.queue_sequence.empty() == False:
					# start a new sequence if no abort sequence requested
					if self.abort_sequences_requested == False:
						self.current_sequence = self.queue_sequence.get()
						self.log_message.emit(utils.timestamp() + 'Execute ' + self.current_sequence.sequence_name + ', round ' + str(self.current_sequence.round))
						QApplication.processEvents()
						self.sequence_started = True
					# abort sequence is requested
					else:
						while self.queue_sequence.empty() == False:
							self.current_sequence = self.queue_sequence.get()
							self.log_message.emit(utils.timestamp() + '! ' + self.current_sequence.sequence_name + ', round ' + str(self.current_sequence.round) + ' aborted')
							QApplication.processEvents()
							self.current_sequence.sequence_started = False
							# void the sequence
							self.current_sequence = None 
	            # if the queue is empty, set the sequences_in_progress flag to False
				else:
					self.sequences_in_progress = False
					if PRINT_DEBUG_INFO:
						print('no more sequences in the queue')
			else:
				return # wait for the current sequence to complete execution

	def _check_microcontroller_state(self):
		# check the microcontroller state, if mcu cmd execution has completed, send new mcu cmd in the queue
		msg = self.microcontroller.read_received_packet_nowait()
		if msg is None:
			return
		# parse packet, step 0: display parsed packet (to add)
		MCU_received_command_UID = (msg[0] << 8) + msg[1] # the parentheses around << is necessary !!!
		MCU_received_command = msg[2]
		MCU_command_execution_status = msg[3]
		MCU_waiting_for_the_first_cmd = (MCU_received_command_UID == 0) and (MCU_received_command==0)

		# step 1: check if MCU is "up to date" with the computer in terms of command
		if (MCU_received_command_UID != self.computer_to_MCU_command_counter) or (MCU_received_command != self.computer_to_MCU_command):
			if PRINT_DEBUG_INFO:
					print('computer\t UID = ' + str(self.computer_to_MCU_command_counter) + ', CMD = ' + str(self.computer_to_MCU_command))
					print('MCU\t\t UID = ' + str(MCU_received_command_UID) + ', CMD = ' + str(MCU_received_command))
					print('----------------')
			if self.timestamp_last_computer_mcu_mismatch == None:
				self.timestamp_last_computer_mcu_mismatch = time.time() # new mismatch, record time stamp
				if PRINT_DEBUG_INFO:
					print('a new MCU received cmd out of sync with computer cmd occured')
			else:
				t_diff = time.time() - self.timestamp_last_computer_mcu_mismatch
				if t_diff > T_DIFF_COMPUTER_MCU_MISMATCH_FAULT_THRESHOLD_SECONDS:
					print('Fault! MCU and computer out of sync for more than 3 seconds')
					# @@@@@ to-do: add error handling @@@@@ #
			return
		else:
			self.timestamp_last_computer_mcu_mismatch = None

		# step 2: check command execution on MCU
		if (MCU_command_execution_status != CMD_EXECUTION_STATUS.IN_PROGRESS) and (MCU_command_execution_status != CMD_EXECUTION_STATUS.COMPLETED_WITHOUT_ERRORS):
			print('cmd execution error, status code: ' + str(MCU_command_execution_status))
			# @@@@@ to-do: add error handling @@@@@ #
			return
		if MCU_command_execution_status == CMD_EXECUTION_STATUS.IN_PROGRESS:
			# the commented section below is not necessary, as when MCU_received_command_UID and MCU_received_command are set or initialized to 0, 
			# MCU_command_execution_status will also be set to CMD_EXECUTION_STATUS.COMPLETED_WITHOUT_ERRORS, 
			# i.e. under no circumstances, CMD_EXECUTION_STATUS.IN_PROGRESS would occur when MCU_received_command_UID == 0 and MCU_received_command == 0
			'''
			if MCU_received_command_UID == 0 and MCU_received_command == 0:
				pass # wait for the first command -> go ahead to load new command
			else:
				# command execution in progress
				if PRINT_DEBUG_INFO:
					print('cmd being executed on the MCU')
				return 
			'''
			# command execution in progress
			if PRINT_DEBUG_INFO:
				print('cmd being executed on the MCU')
			return 
		if MCU_command_execution_status == CMD_EXECUTION_STATUS.COMPLETED_WITHOUT_ERRORS:
			# command execucation has completed, can move to the next command
			pass # go ahead to load new command
	
		# step 3: send the new command to MCU
		if self.queque_to_Microcontroller_Command.empty() == False:
			# get the new command to execute
			cmd = self.queque_to_Microcontroller_Command.get()
			self.computer_to_MCU_command_counter = self.computer_to_MCU_command_counter + 1
			self.computer_to_MCU_command = cmd[2]
			# send the command to the microcontroller
			cmd_with_uid = self._add_UID_to_mcu_command_packet(cmd,self.computer_to_MCU_command_counter)
			self.microcontroller.send_command(cmd_with_uid)

	def add_sequence(self,sequence_name,fluidic_port,flow_time_s,incubation_time_min,pressure_setting=None,round_=1):
		print('adding sequence to the queue ' + sequence_name + ' - flow time: ' + str(flow_time_s) + ' s, incubation time: ' + str(incubation_time_min) + ' s [negative number means no removal]')
		sequence_to_add = Sequence(sequence_name,fluidic_port,flow_time_s,incubation_time_min,pressure_setting,round_)
		self.queue_sequence.put(sequence_to_add)
		self.abort_sequences_requested = False
		self.sequences_in_progress = True		
			
	def request_abort_sequences(self):
		self.abort_sequences_requested = True


class Logger(QObject):

	def __init__(self,filepath = os.path.join(Path.home(),"Documents","starmap-automation logs.txt")):
		QObject.__init__(self)
		self.file = open(filepath,'a')

	def log(self,log_message):
		self.file.write(log_message + '\n')

	def __del__(self):
		self.file.close()
		
	def close(self):
		self.file.close()