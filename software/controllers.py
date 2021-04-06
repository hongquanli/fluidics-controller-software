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
		# clear counter

		# for simulation 
		self.timer_update_command_execution_status = QTimer()
		self.cmd_status = 0
	
	def __del__(self):
		pass

	def read_received_packet_nowait(self):
		data=[]
		for i in range(self.rx_buffer_length):
			data.append(0)
		data[3] = self.cmd_status
		return data

	def send_command(self,cmd):
		self.cmd_status = 0
		self.timer_update_command_execution_status.setInterval(2000)
		self.timer_update_command_execution_status.start()
		print(cmd)

	def update_cmd_status(self):
		print('simulation - MCU command execution finished')
		self.cmd_status = 1
		self.timer_update_command_execution_status.stop()

###################################################
################# FluidController #################
###################################################

import queue

class FluidController(QObject):
	
	log_message = Signal(str)

	def __init__(self,microcontroller):
		QObject.__init__(self)
		self.microcontroller = microcontroller		
		self.cmd_length = MCU_CMD_LENGTH

		# clear counter on both the computer and the MCU
		self.computer_to_MCU_command_counter = 0
		self.computer_to_MCU_command = C2M_CLEAR # when init the MCU in the firmware, set computer_to_MCU_command = 255 (reserved), so that there will be mismatch until proper communication
		cmd = self._format_command(self.computer_to_MCU_command)
		cmd = self._add_UID_to_command(cmd,self.computer_to_MCU_command_counter)
		self.microcontroller.send_command(cmd)

		self.sequences_abort_requested = False
		self.sequence_in_progress = False
		self.to_microcontroller_command_queque = queue.Queue()

		self.timer_check_microcontroller_state = QTimer()
		self.timer_check_microcontroller_state.setInterval(TIMER_CHECK_MCU_STATE_INTERVAL_MS)
		self.timer_check_microcontroller_state.timeout.connect(self._check_microcontroller_state)
		self.timer_check_microcontroller_state.start()

		self.timestamp_last_computer_mcu_mismatch = None

	def _format_command(self,command,payload1=0,payload2=0):
		cmd = bytearray(self.cmd_length)
		cmd[0] = 0
		cmd[1] = 0
		cmd[2] = command
		cmd[3] = payload1 >> 8
		cmd[4] = payload1 & 0xff
		cmd[5] = payload1 >> 8
		cmd[6] = payload1 & 0xff
		return cmd

	def _add_UID_to_command(self,cmd,command_UID):
		cmd[0] = command_UID >> 8
		cmd[1] = command_UID & 0xff
		return cmd

	def _check_microcontroller_state(self):
		packet = self.microcontroller.read_received_packet_nowait()
		if packet is None:
			return
		# parse packet, step 0: display parsed packet (to add)
		MCU_received_command_UID = packet[0] << 8 + packet[1]
		MCU_received_command = packet[2]
		MCU_command_execution_status = packet[3]

		# step 1: check if MCU is "up to date" with the computer in terms of command
		if (MCU_received_command_UID != self.computer_to_MCU_command_counter) or (MCU_received_command != self.computer_to_MCU_command):
			print('mismatch')
			if self.timestamp_last_computer_mcu_mismatch == None:
				self.timestamp_last_computer_mcu_mismatch = time.time() # new mismatch, record time stamp
			else:
				t_diff = time.time() - self.timestamp_last_computer_mcu_mismatch
				if t_diff > T_DIFF_COMPUTER_MCU_MISMATCH_FAULT_THRESHOLD_SECONDS:
					print('Fault! MCU and computer out of sync for more than 3 seconds')
					# @@@@@ to-do: add error handling @@@@@ #
					return
		if (MCU_received_command_UID == self.computer_to_MCU_command_counter) and (MCU_received_command == self.computer_to_MCU_command):
			self.timestamp_last_computer_mcu_mismatch = None

		# step 2: check command execution on MCU
		if MCU_command_execution_status > 1:
			# @@@@@ to-do: add error handling @@@@@ #
			print('cmd execution error')
			return
		if MCU_command_execution_status == 1 or ( MCU_received_command_UID == 0 and MCU_received_command == 0): # @@@ to do - improve this line
			# command execucation has completed, can move to the next command
			if self.to_microcontroller_command_queque.empty() == False:
				cmd = self.to_microcontroller_command_queque.get()
			else:
				return
		if MCU_command_execution_status == 0:
			return

		# step 3: send the new command to MCU
		self.computer_to_MCU_command_counter = self.computer_to_MCU_command_counter + 1
		cmd = self._add_UID_to_command(self,cmd,self.computer_to_MCU_command_counter)
		self.microcontroller.send_command(cmd)
		print('sending the next command')
		

	def run_sequence(self,sequence_name,fluidic_port,flow_time,incubation_time):
		print(sequence_name + ' - flow time: ' + str(flow_time) + ' s, incubation time: ' + str(incubation_time) + ' s [negative number means no removal]')
		self.sequences_abort_requested = False
		self.sequence_in_progress = True
		# incubation time - negative number means no removal
		# handle different types of sequences
		# case 1: strip, wash (post-strip), ligate, wash (post-ligate)
		# case 2: add imaging buffer, (stain with DAPI)
		# case 3: remove imaging buffer (can apply to removing any other liquid)

		cmd_0 = self._format_command(1,1,1);
		cmd_1 = self._format_command(2,2,2);
		cmd_2 = self._format_command(3,3,3);
		self.to_microcontroller_command_queque.put(cmd_0)
		self.to_microcontroller_command_queque.put(cmd_1)
		self.to_microcontroller_command_queque.put(cmd_2)

		if flow_time <= 0: # case 3, remove liquid
			pass
			
	def request_abort_sequences(self):
		self.sequences_abort_requested = True

		'''
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()
		'''



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