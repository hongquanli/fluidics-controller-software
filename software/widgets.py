# set QT_API environment variable
import os 
os.environ["QT_API"] = "pyqt5"
import qtpy

# qt libraries
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

# app specific libraries
from datetime import datetime
import threading
import utils
from _def import * 

class PreUseCheckWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):
        # add checkboxes for ports to be primed 
        self.checkbox_wash_buffer = QCheckBox('wash buffer')
        self.checkbox_imaging_buffer = QCheckBox('imaging buffer')
        self.checkbox_strip_buffer = QCheckBox('strip buffer')
        self.checkbox_ligation_buffer_1 = QCheckBox('1')
        self.checkbox_ligation_buffer_2 = QCheckBox('2')
        self.checkbox_ligation_buffer_3 = QCheckBox('3')
        self.checkbox_ligation_buffer_4 = QCheckBox('4')
        self.checkbox_ligation_buffer_5 = QCheckBox('5')
        self.checkbox_ligation_buffer_6 = QCheckBox('6')
        self.checkbox_DAPI = QCheckBox('DAPI')
        self.checkbox_Nissl = QCheckBox('Nissl')

        self.checkbox_wash_buffer.setChecked(True)
        self.checkbox_imaging_buffer.setChecked(True)
        self.checkbox_strip_buffer.setChecked(True)
        self.checkbox_ligation_buffer_1.setChecked(len(LIGATION.PORTS)>=1)
        self.checkbox_ligation_buffer_2.setChecked(len(LIGATION.PORTS)>=2)
        self.checkbox_ligation_buffer_3.setChecked(len(LIGATION.PORTS)>=3)
        self.checkbox_ligation_buffer_4.setChecked(len(LIGATION.PORTS)>=4)
        self.checkbox_ligation_buffer_5.setChecked(len(LIGATION.PORTS)>=5)
        self.checkbox_ligation_buffer_6.setChecked(len(LIGATION.PORTS)>=6)
        self.checkbox_DAPI.setChecked(DAPI.IS_PRESENT)
        self.checkbox_Nissl.setChecked(NISSL.IS_PRESENT)

        # add buttons
        self.button_prime_ports_through_bypass = QPushButton('Prime ports')
        self.button_prime_flowcell = QPushButton('Prime flow cell with wash buffer') 
        self.button_prime_flowcell.setEnabled(False) # flow cell priming does not work for FCS2 chamber (at least not for 14x24 0.25mm thick gasket - experiments done on 10/24/2020; might work for narrower channels)
        
        self.button_prime_ports_through_bypass.setCheckable(True)
        self.button_prime_flowcell.setCheckable(True)
        
        self.button_prime_ports_through_bypass.clicked.connect(self.prime_ports_through_bypass)
        self.button_prime_flowcell.clicked.connect(self.prime_flowcell)

        hbox_1 = QHBoxLayout()
        hbox_1.addWidget(self.checkbox_wash_buffer)
        hbox_1.addWidget(self.checkbox_imaging_buffer)
        hbox_1.addWidget(self.checkbox_strip_buffer)
        hbox_1.addWidget(self.checkbox_ligation_buffer_1)
        hbox_1.addWidget(self.checkbox_ligation_buffer_2)
        hbox_1.addWidget(self.checkbox_ligation_buffer_3)
        hbox_1.addWidget(self.checkbox_ligation_buffer_4)
        hbox_1.addWidget(self.checkbox_ligation_buffer_5)
        hbox_1.addWidget(self.checkbox_ligation_buffer_6)
        hbox_1.addWidget(self.checkbox_DAPI)
        hbox_1.addWidget(self.checkbox_Nissl)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_1)
        vbox.addWidget(self.button_prime_ports_through_bypass)
        vbox.addWidget(self.button_prime_flowcell)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('[Pre-use Check]]'))
        hbox.addLayout(vbox)

        self.setLayout(hbox)

    def prime_ports_through_bypass(self,pressed):
        if pressed:
            if self.checkbox_wash_buffer.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming wash buffer port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,WASH.PORT)

            if self.checkbox_imaging_buffer.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming imaging buffer port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,IMAGING_BUFFER.PORT)

            if self.checkbox_strip_buffer.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming strip buffer port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,STRIP.PORT)

            if self.checkbox_ligation_buffer_1.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming ligation buffer 1 port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,LIGATION.PORTS[0])

            if self.checkbox_ligation_buffer_2.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming ligation buffer 2 port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,LIGATION.PORTS[1])

            if self.checkbox_ligation_buffer_3.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming ligation buffer 3 port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,LIGATION.PORTS[2])

            if self.checkbox_ligation_buffer_4.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming ligation buffer 4 port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,LIGATION.PORTS[3])

            if self.checkbox_ligation_buffer_5.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming ligation buffer 5 port')
                QApplication.processEvents()
                result = self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,LIGATION.PORTS[4])

            if self.checkbox_ligation_buffer_6.isChecked():
                self.log_message.emit(utils.timestamp() + 'priming ligation buffer 6 port')
                QApplication.processEvents()
                self.fluidController.prime_selector_valve_port(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,LIGATION.PORTS[5])
            self.button_prime_ports_through_bypass.setChecked(False)

                #thread = threading.Thread(target=self.fluidController.prime_selector_valve_port,args=(BYPASS.TRUE,PRIMING.FLOW_RATE_UL_PER_SECOND,WASH.PORT))
                #thread.start()
                #thread.join()
                #print('prime the wash buffer port')

    def prime_flowcell(self,pressed):
        if pressed:
            self.log_message.emit(utils.timestamp() + 'priming flow cell')
            QApplication.processEvents()
            self.fluidController.prime_selector_valve_port(BYPASS.FALSE,PRIMING.FLOW_RATE_UL_PER_SECOND,WASH.PORT)
            self.button_prime_flowcell.setChecked(False)

class CoverGlassLoadingWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):
        self.button_prepare_for_sample_loading = QPushButton('Prefill the Flow Cell Inlet Tubing')
        self.button_prepare_for_sample_loading.clicked.connect(self.prepare_for_sample_loading)
        hbox = QHBoxLayout() 
        hbox.addWidget(QLabel('[Sample Loading]'))
        hbox.addWidget(self.button_prepare_for_sample_loading)
        self.setLayout(hbox)

    def prepare_for_sample_loading(self,pressed):
        self.log_message.emit(utils.timestamp() + 'prefill the flow cell inlet tubing for sample loading.')
        QApplication.processEvents()
        self.fluidController.prepare_for_sample_loading()


class TriggerWidget(QFrame):

    def __init__(self, triggerController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.triggerController = triggerController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):
        self.button_trigger_microscope = QPushButton('Trigger Microscope')
        self.button_trigger_microscope.clicked.connect(self.trigger_microscope)
        hbox = QHBoxLayout() 
        hbox.addWidget(QLabel('[Manual Microscope Trigger]'))
        hbox.addWidget(self.button_trigger_microscope)
        self.setLayout(hbox)

    def trigger_microscope(self,pressed):
        #if pressed:
        self.triggerController.send_trigger()

class ManualFlowWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):
        self.entry_port = QSpinBox()
        self.entry_port.setMinimum(0) 
        self.entry_port.setMaximum(20) 
        self.entry_port.setSingleStep(1)
        self.entry_port.setValue(1)

        self.entry_volume_ul = QDoubleSpinBox()
        self.entry_volume_ul.setMinimum(0)
        self.entry_volume_ul.setMaximum(1000) 
        self.entry_volume_ul.setSingleStep(5)
        self.entry_volume_ul.setValue(50)

        self.entry_flowrate_ul_per_s = QDoubleSpinBox()
        self.entry_flowrate_ul_per_s.setMinimum(0) 
        self.entry_flowrate_ul_per_s.setMaximum(35) 
        self.entry_flowrate_ul_per_s.setSingleStep(0.1)
        self.entry_flowrate_ul_per_s.setValue(1)

        self.checkbox_bypass = QCheckBox('bypass')

        self.button_flow_fluid = QPushButton('Flow Fluid')
        self.button_flow_fluid.clicked.connect(self.flow_fluid)
        
        hbox = QHBoxLayout() 
        hbox.addWidget(QLabel('[Manual Flow]'))
        hbox.addWidget(QLabel('Port'))
        hbox.addWidget(self.entry_port)
        hbox.addWidget(QLabel('Volume (uL)'))
        hbox.addWidget(self.entry_volume_ul)
        hbox.addWidget(QLabel('Flowrate (uL/s)'))
        hbox.addWidget(self.entry_flowrate_ul_per_s)
        hbox.addWidget(self.checkbox_bypass)
        hbox.addWidget(self.button_flow_fluid)
        self.setLayout(hbox)

    def flow_fluid(self):
        if self.checkbox_bypass.isChecked() == True:
            bypass = BYPASS.TRUE
            flow_through = 'by pass'
        else:
            bypass = BYPASS.FALSE
            flow_through = 'flow cell'
        volume_ul = self.entry_volume_ul.value()
        flowrate_ul_per_s = self.entry_flowrate_ul_per_s.value()
        port = self.entry_port.value()


        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("Confirm your action")
        msg.setInformativeText("Click OK to flow " + str(volume_ul) + " ul from port " + str(port) + " through " + flow_through + ", which will take " + "{:.1f}".format(volume_ul/flowrate_ul_per_s/60) + " min." )
        msg.setWindowTitle("Confirmation")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
    
        retval = msg.exec_()
        if QMessageBox.Ok == retval:
            self.log_message.emit(utils.timestamp() + 'flow ' + str(volume_ul) + ' ul buffer from port ' + str(port) + ' through ' + flow_through + ' at ' + str(flowrate_ul_per_s) + ' ul/s.')
            QApplication.processEvents()
            self.fluidController.flow(volume_ul,flowrate_ul_per_s,port,bypass)
            self.log_message.emit(utils.timestamp() + 'swith flow path to bypass to prevent fluid from continuing to flow into the flow cell due to capilary action.')
            QApplication.processEvents()
            self.fluidController.switch_flow_path_to_bypass()
        else:
            self.log_message.emit(utils.timestamp() + 'no action.')
            QApplication.processEvents()

class ManualFlushWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):

        self.entry_volume_ul = QDoubleSpinBox()
        self.entry_volume_ul.setMinimum(0)
        self.entry_volume_ul.setMaximum(1000) 
        self.entry_volume_ul.setSingleStep(5)
        self.entry_volume_ul.setValue(BLEACH.FLOW_VOLUME_UL)

        self.entry_flowrate_ul_per_s = QDoubleSpinBox()
        self.entry_flowrate_ul_per_s.setMinimum(0) 
        self.entry_flowrate_ul_per_s.setMaximum(20) 
        self.entry_flowrate_ul_per_s.setSingleStep(0.1)
        self.entry_flowrate_ul_per_s.setValue(BLEACH.FLOW_RATE_UL_PER_SECOND)

        self.checkbox_bypass = QCheckBox('bypass')

        self.button_bleach = QPushButton('Bleach')
        self.button_bleach.clicked.connect(self.bleach)
        
        hbox = QHBoxLayout() 
        hbox.addWidget(QLabel('[Manual Bleach]'))
        hbox.addWidget(QLabel('Volume (uL)'))
        hbox.addWidget(self.entry_volume_ul)
        hbox.addWidget(QLabel('Flowrate (uL/s)'))
        hbox.addWidget(self.entry_flowrate_ul_per_s)
        hbox.addWidget(self.checkbox_bypass)
        hbox.addWidget(self.button_bleach)
        self.setLayout(hbox)

    def bleach(self):
        if self.checkbox_bypass.isChecked() == True:
            bypass = BYPASS.TRUE
            flow_through = 'by pass'
        else:
            bypass = BYPASS.FALSE
            flow_through = 'flow cell'
        volume_ul = self.entry_volume_ul.value()
        flowrate_ul_per_s = self.entry_flowrate_ul_per_s.value()
        self.log_message.emit(utils.timestamp() + 'flow ' + str(volume_ul) + ' ul bleach through ' + flow_through + ' at ' + str(flowrate_ul_per_s) + ' ul/s.')
        QApplication.processEvents()
        self.fluidController.bleach(bypass,volume_ul,flowrate_ul_per_s)


class ExperimentWidget(QFrame):

    def __init__(self, experimentController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.experimentController = experimentController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):
        self.button_run_experiment = QPushButton('Run Experiment')
        self.button_run_experiment.clicked.connect(self.experimentController.run_experiment)
        hbox = QHBoxLayout() 
        hbox.addWidget(QLabel('[Automated Experiment]'))
        hbox.addWidget(self.button_run_experiment)
        self.setLayout(hbox)
        self.button_run_experiment.setEnabled(False) # disabled until the fluidic handling is made more robust

class ChillerWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):

        self.entry_temperature = QDoubleSpinBox()
        self.entry_temperature.setMinimum(0)
        self.entry_temperature.setMaximum(25) 
        self.entry_temperature.setSingleStep(1)
        self.entry_temperature.setValue(4)

        self.button_set_temp = QPushButton('Set Temperature')
        self.button_check_temp = QPushButton('Check Temperature')
        self.button_set_temp.clicked.connect(self.set_chiller_temperature)
        self.button_check_temp.clicked.connect(self.check_chiller_temperature)
        
        hbox = QHBoxLayout() 
        hbox.addWidget(QLabel('[Chiller]'))
        hbox.addWidget(QLabel('Temperature (degree C)'))
        hbox.addWidget(self.entry_temperature)
        hbox.addWidget(self.button_set_temp)
        hbox.addWidget(self.button_check_temp)
        self.setLayout(hbox)

    def set_chiller_temperature(self):
        temperature = self.entry_temperature.value()
        self.log_message.emit(utils.timestamp() + 'set chiller temperature to ' + str(temperature) + ' degree C.')
        QApplication.processEvents()
        self.fluidController.set_chiller_temperature(temperature)

    def check_chiller_temperature(self):
        self.log_message.emit(utils.timestamp() + 'check chiller temperature.')
        QApplication.processEvents()
        self.fluidController.check_chiller_temperature()

class SwitchToBypassWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):

        self.button_switch_to_bypass = QPushButton('Switch Flow Path to Bypass')
        self.button_switch_to_bypass.clicked.connect(self.switch_flow_path_to_bypass)
        
        hbox = QHBoxLayout() 
        hbox.addWidget(QLabel('[Switch Flow Path to Bypass]'))
        hbox.addWidget(self.button_switch_to_bypass)
        self.setLayout(hbox)

    def switch_flow_path_to_bypass(self):
        self.log_message.emit(utils.timestamp() + 'switch flow path to bypass.')
        QApplication.processEvents()
        self.fluidController.switch_flow_path_to_bypass()