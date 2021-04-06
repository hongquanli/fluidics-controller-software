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

def _convert_volume_to_steps(volume):
	return 
def _convert_speed_to_4steps(flow_rate_ul_per_s):
	return 
def _convert_to_hex_string(number):
	return format(number,'02X')

class fluid_controller(object):
	def __init__(self):
		controller_ports = [
				p.device
				for p in serial.tools.list_ports.comports()
				#if 'USB-Serial Controller D' in p.description] # for Mac
				if 'Prolific' in p.description] # for windows
		if not controller_ports:
			raise IOError("No Controller Found")
		self.serial = serial.Serial(controller_ports[0],9600)
		utils.print_message('Fluid Controller Connected')
	
	def __del__(self):
		self.serial.close()


class FluidController(QObject):
	
	log_message = Signal(str)

	def __init__(self):
		QObject.__init__(self)
		self.fluid_controller = fluid_controller()
		self.sequences_abort_requested = False

		'''
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()
		'''

	def run_sequence(self,sequence_name,flow_time,incubation_time):
		self.sequences_abort_requested = False
		# incubation time - negative number means no removal
		print(sequence_name + ' - flow time: ' + str(flow_time) + ' s, incubation time: ' + str(incubation_time) + ' s [negative number means no removal]')

	def request_abort_sequences(self):
		self.sequences_abort_requested = True

class FluidController_simulation(QObject):
	
	log_message = Signal(str)

	def __init__(self):
		QObject.__init__(self)
		self.sequences_abort_requested = False

	def run_sequence(self,sequence_name,flow_time,incubation_time):
		# incubation time - negative number means no removal
		self.sequences_abort_requested = False
		print(sequence_name + ' - flow time: ' + str(flow_time) + ' s, incubation time: ' + str(incubation_time) + ' s [negative number means no removal]')

	def request_abort_sequences(self):
		self.sequences_abort_requested = True


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