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

	def _send_command(self,command_string):
		command_string = command_string + '\r\n'
		self.serial.write(command_string.encode())

	def _wait_until_operation_is_complete(self,timeout_min=60):
		return

	def _select_valve_port(self,valve_port):
		valve_port_hex_string = _convert_to_hex_string(valve_port)
		command_string = 'VP' + valve_port_hex_string
		self._send_command(command_string)
		return self._wait_until_operation_is_complete()

	def bleach(self,bypass,volume_ul = 0,flow_rate_ul_per_s = 0):
		return 'operation completed'

	def flow(self,volume_ul,flow_rate_ul_per_s,valve_port,bypass):
		return 'operation completed'

	def prime_selector_valve_port(self,bypass,flow_rate_ul_per_s,valve_port):
		utils.print_message(' - Prime Port ' + str(valve_port))
		speed_4stpes = _convert_speed_to_4steps(flow_rate_ul_per_s)
		valve_port_hex_string = _convert_to_hex_string(valve_port)
		command_string = 'M2' + ',' + bypass + ',' + str(int(speed_4stpes)) + ',' + valve_port_hex_string
		self._send_command(command_string)
		return self._wait_until_operation_is_complete()

	def connect_flowcell_to_wash_buffer(self):
		return 

	def prepare_for_sample_loading(self):
		return

	def set_chiller_temperature(self,temperature):
		command_string = 'Cn' + '{:04.1f}'.format(temperature)
		self._send_command(command_string)
		return self._wait_until_operation_is_complete() 

	def check_chiller_temperature(self):
		command_string = 'Cp'
		self._send_command(command_string)
		return self._wait_until_operation_is_complete() 

	def switch_flow_path_to_bypass(self):
		command_string = 'S1'
		self._send_command(command_string)
		return self._wait_until_operation_is_complete() 

class FluidController(QObject):
	
	log_message = Signal(str)

	def __init__(self):
		QObject.__init__(self)
		self.fluid_controller = fluid_controller()
		self.sequences_abort_requested = False

	def prime_selector_valve_port(self,bypass,flow_rate_ul_per_s,valve_port):
		status = self.fluid_controller.prime_selector_valve_port(bypass,flow_rate_ul_per_s,valve_port)
		self.log_message.emit(utils.timestamp() + status)
		# self.log_message.emit('')
		QApplication.processEvents()

	def flow(self,volume_ul,flow_rate_ul_per_s,valve_port,bypass):
		status = self.fluid_controller.flow(volume_ul,flow_rate_ul_per_s,valve_port,bypass)
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def bleach(self,bypass,volume_ul,flow_rate_ul_per_s):
		status = self.fluid_controller.bleach(bypass,volume_ul,flow_rate_ul_per_s)
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def connect_flowcell_to_wash_buffer(self):
		status = self.fluid_controller.connect_flowcell_to_wash_buffer()
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def prepare_for_sample_loading(self):
		status = self.fluid_controller.prepare_for_sample_loading()
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def set_chiller_temperature(self,temperature):
		status = self.fluid_controller.set_chiller_temperature(temperature)
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def check_chiller_temperature(self):
		status = self.fluid_controller.check_chiller_temperature()
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def switch_flow_path_to_bypass(self):
		status = self.fluid_controller.switch_flow_path_to_bypass()
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

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
		
	def prime_selector_valve_port(self,bypass,flow_rate_ul_per_s,valve_port):
		status = 'completed'
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def flow(self,volume_ul,flow_rate_ul_per_s,valve_port,bypass):
		status = 'completed'
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def bleach(self,bypass,volume_ul,flow_rate_ul_per_s):
		status = 'completed'
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def connect_flowcell_to_wash_buffer(self):
		status = 'completed'
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def prepare_for_sample_loading(self):
		status = 'completed'
		self.log_message.emit(utils.timestamp() + status)
		QApplication.processEvents()

	def switch_flow_path_to_bypass(self):
		time.sleep
		pass

	def run_sequence(self,sequence_name,flow_time,incubation_time):
		# incubation time - negative number means no removal
		self.sequences_abort_requested = False
		print(sequence_name + ' - flow time: ' + str(flow_time) + ' s, incubation time: ' + str(incubation_time) + ' s [negative number means no removal]')

	def request_abort_sequences(self):
		self.sequences_abort_requested = True

class ExperimentController(QObject):

	log_message = Signal(str)

	def __init__(self,triggerController,fluidController):
		QObject.__init__(self)
		self.triggerController = triggerController
		self.fluidController = fluidController

		self.number_of_rounds = NUMBER_OF_ROUNDS

	def flow_ligase_enzyme_mixture(self,i):
		self.log_message.emit(utils.timestamp() + 'flow ligation buffer')
		QApplication.processEvents()
		self.fluidController.flow(LIGATION.FLOW_VOLUME_UL,LIGATION.FLOW_RATE_UL_PER_SECOND,LIGATION.PORTS[i],BYPASS.FALSE)

	def flow_wash_buffer_preimaging(self):
		self.log_message.emit(utils.timestamp() + 'flow wash buffer (preimaging)')
		QApplication.processEvents()
		self.fluidController.flow(WASH_PREIMAGING.FLOW_VOLUME_UL,WASH_PREIMAGING.FLOW_RATE_UL_PER_SECOND,WASH_PREIMAGING.PORT,BYPASS.FALSE)

	def flow_wash_buffer_postimaging(self):
		self.log_message.emit(utils.timestamp() + 'flow wash buffer (postimaging)')
		QApplication.processEvents()
		self.fluidController.flow(WASH_POSTIMAGING.FLOW_VOLUME_UL,WASH_POSTIMAGING.FLOW_RATE_UL_PER_SECOND,WASH_POSTIMAGING.PORT,BYPASS.FALSE)

	def flow_imaging_buffer(self):
		self.log_message.emit(utils.timestamp() + 'flow imaging buffer')
		QApplication.processEvents()
		self.fluidController.flow(IMAGING_BUFFER.FLOW_VOLUME_UL,IMAGING_BUFFER.FLOW_RATE_UL_PER_SECOND,IMAGING_BUFFER.PORT,BYPASS.FALSE)

	def flow_strip_buffer(self):
		self.log_message.emit(utils.timestamp() + 'flow strip buffer')
		QApplication.processEvents()
		self.fluidController.flow(STRIP.FLOW_VOLUME_UL,STRIP.FLOW_RATE_UL_PER_SECOND,STRIP.PORT,BYPASS.FALSE)

	def flow_Nissl(self):
		self.log_message.emit(utils.timestamp() + 'flow Nissl staining buffer')
		QApplication.processEvents()
		self.flow_flowcell(NISSL.FLOW_VOLUME_UL,NISSL.FLOW_RATE_UL_PER_SECOND,NISSL.PORT,BYPASS.FALSE)

	def flow_DAPI(self):
		self.log_message.emit(utils.timestamp() + 'flow DAPI staining buffer')
		QApplication.processEvents()
		self.flow_flowcell(DAPI.FLOW_VOLUME_UL,DAPI.FLOW_RATE_UL_PER_SECOND,DAPI.PORT,BYPASS.FALSE)

	def run_experiment(self):
		# @@@@TODO: launch a dialog for the user to confirm that the system has been primed
		for i in range(self.number_of_rounds):
			self.log_message.emit(utils.timestamp() + '<<< Start Round ' + str(i+1) + ' >>>')
			# flow ligation buffer
			self.flow_ligase_enzyme_mixture(i)
			# incubate
			self.log_message.emit(utils.timestamp() + 'Incubate for ' + str(LIGATION.INCUBATION_TIME_MIN/60) + ' hours')
			# time.sleep(LIGATION.INCUBATION_TIME_MIN*60)
			# flow wash buffer
			self.flow_wash_buffer_preimaging()
			# flow imaging buffer
			self.flow_imaging_buffer()
			# trigger microscope
			self.triggerController.send_trigger()
			# wait for imaging to complete
			while(self.triggerController.trigger_received == False):
				time.sleep(1)
				QApplication.processEvents()
			self.triggerController.trigger_received = False
			# flow strip buffer
			self.flow_strip_buffer()
			# flow wash buffer
			self.flow_wash_buffer_postimaging()
		# @@@TODO: more steps to be added; Make it more interactive - e.g. pause, redo


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