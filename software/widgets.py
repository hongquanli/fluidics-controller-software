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
        
        # create and layout the checkboxes
        hbox_1 = QHBoxLayout()
        num_ports = len(Ports_Name)
        self.checkbox = []
        for i in range(num_ports):
            self.checkbox.append(QCheckBox(Ports_Name[i]))
            self.checkbox[i].setChecked(True)
            hbox_1.addWidget(self.checkbox[i])

        # target pressure 
        self.entry_target_pressure = QDoubleSpinBox()
        self.entry_target_pressure.setMinimum(0)
        self.entry_target_pressure.setMaximum(5.0) 
        self.entry_target_pressure.setSingleStep(0.1)
        self.entry_target_pressure.setValue(4.0)
        hbox_2 = QHBoxLayout()
        hbox_2.addWidget(QLabel('Target Pressure (psi)'))
        hbox_2.addWidget(self.entry_target_pressure)

        # target vacuum 
        self.entry_target_vacuum = QDoubleSpinBox()
        self.entry_target_vacuum.setMinimum(-4.0)
        self.entry_target_vacuum.setMaximum(0) 
        self.entry_target_vacuum.setSingleStep(0.1)
        self.entry_target_vacuum.setValue(-3.0)
        # hbox_3 = QHBoxLayout()
        hbox_2.addWidget(QLabel('\t Target Vacuum (psi)'))
        hbox_2.addWidget(self.entry_target_vacuum)
       
        # add buttons
        self.button_preuse_check = QPushButton('Run Pre-Use Check')
        self.button_preuse_check.setCheckable(True)
        self.button_preuse_check.clicked.connect(self.run_preuse_check)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox_1)
        vbox.addLayout(hbox_2)
        vbox.addWidget(self.button_preuse_check)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('[Pre-use Check]]'))
        hbox.addLayout(vbox)

        self.setLayout(hbox)

    def run_preuse_check(self,pressed):
        if pressed:
            for i in range(len(Ports_Name)):
                if(self.checkbox[i].isChecked()==True):
                    print('checking port ' + Ports_Name[i] )
                    self.log_message.emit(utils.timestamp() + 'checking port ' + Ports_Name[i])
                    QApplication.processEvents()
                else:
                    pass
        self.button_preuse_check.setChecked(False)
        QApplication.processEvents()


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

class SequenceEntry(QWidget):
    def __init__(self, sequence_name = None, port_name = None, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sequence_name = sequence_name
        self.port_name = port_name
        '''
        # using list 
        self.attributes = []
        self.attributes.append(QLabel(self.sequence_name))
        self.attributes.append(QCheckBox('Include'))
        self.attributes.append(QDoubleSpinBox())
        self.attributes.append(QDoubleSpinBox()) # incubation_time
        self.attributes.append(QSpinBox()) # repeat
        '''
        # using dictionary
        self.attributes_key = SEQUENCE_ATTRIBUTES_KEYS
        self.attributes = {}
        self.attributes['Label'] = QLabel(self.sequence_name)
        self.attributes['Include'] = QCheckBox()
        self.attributes['Flow Time (s)'] = QDoubleSpinBox()
        self.attributes['Flow Time (s)'].setMinimum(1)
        self.attributes['Flow Time (s)'].setMaximum(FLOW_TIME_MAX)
        self.attributes['Incubation Time (s)'] = QDoubleSpinBox()
        self.attributes['Incubation Time (s)'].setMinimum(0)
        self.attributes['Incubation Time (s)'].setMaximum(INCUBATION_TIME_MAX)
        self.attributes['Repeat'] = QSpinBox()
        self.attributes['Repeat'].setMinimum(1)
        self.attributes['Repeat'].setMaximum(5)
        # manually make sure the keys are included in SEQUENCE_ATTRIBUTES_KEYS
        
class SequenceWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    # sequences
    '''
    1. strip - volume (time) [1.2 ml] - wait time - number of times [2]
    2. wash (post-strip) - volume (time) [1.2 ml] - wait time - number of cycles [3]
    3. sequencing mixture - all available - wait time
    4. wash (post ligation) - volume (time) - wait time - number of cycles [3]
    4. imaging buffer - volume (time) [1.2 ml]
    5. DAPI - volume (time) [1.2 ml] - wait time
    '''

    def add_components(self):

        tableWidget = QTableWidget(6,5,self)
        tableWidget.setHorizontalHeaderLabels(SEQUENCE_ATTRIBUTES_KEYS)
        
        # create the sequences, set the attributes and add the sequences into the tabel
        self.sequences = {}
        for i in range(len(SEQUENCE_NAME)):
            sequence_name = SEQUENCE_NAME[i]
            self.sequences[sequence_name] = SequenceEntry(sequence_name)
            # insert into the table
            for j in range(len(SEQUENCE_ATTRIBUTES_KEYS)):
                attribute_key = SEQUENCE_ATTRIBUTES_KEYS[j]
                tableWidget.setCellWidget(i,j,self.sequences[sequence_name].attributes[attribute_key])
            # tableWidget.setCellWidget(i,0,self.sequences[sequence_name].attributes['Label'])

        '''
        hbox = QHBoxLayout()
        hbox.addWidget(tableWidget)
        self.setLayout(hbox)
        '''
        
        # button
        self.button_run = QPushButton('Run Selected Sequences')

        vbox = QVBoxLayout()
        vbox.addWidget(tableWidget)
        vbox.addWidget(self.button_run)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('[Sequences]'))
        hbox.addLayout(vbox)
        self.setLayout(hbox)

        '''
        self.sequenceEntry1 = SequenceEntry(sequence_name = 'Strip')
        self.sequenceEntry2 = SequenceEntry(sequence_name = 'Wash (Post-Strip)')
        self.sequenceEntry3 = SequenceEntry(sequence_name = 'Ligate')
        self.sequenceEntry4 = SequenceEntry(sequence_name = 'Wash (Post-Ligation')
        self.sequenceEntry5 = SequenceEntry(sequence_name = 'Add Imaging Buffer')
        self.sequenceEntry6 = SequenceEntry(sequence_name = 'Stain with DAPI')

        self.button_run = QPushButton('Run Selected Sequences')

        grid_layout = QGridLayout()
        grid_layout.addWidget(self.sequenceEntry1,0,0)
        grid_layout.addWidget(self.sequenceEntry2,1,0)
        grid_layout.addWidget(self.sequenceEntry3,2,0)
        grid_layout.addWidget(self.sequenceEntry4,3,0)
        grid_layout.addWidget(self.sequenceEntry5,4,0)
        grid_layout.addWidget(self.sequenceEntry6,5,0)

        vbox = QVBoxLayout()
        vbox.addLayout(grid_layout)
        vbox.addWidget(self.button_run)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('[Sequences]'))
        hbox.addLayout(vbox)
        self.setLayout(hbox)
        '''

        '''
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
        hbox.addWidget(QLabel('[Sequences]'))
        hbox.addWidget(QLabel('Port'))
        hbox.addWidget(self.entry_port)
        hbox.addWidget(QLabel('Volume (uL)'))
        hbox.addWidget(self.entry_volume_ul)
        hbox.addWidget(QLabel('Flowrate (uL/s)'))
        hbox.addWidget(self.entry_flowrate_ul_per_s)
        hbox.addWidget(self.checkbox_bypass)
        hbox.addWidget(self.button_flow_fluid)
        self.setLayout(hbox)
        '''

    def flow_fluid(self):
        pass
        '''
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
    '''

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
        self.entry_volume_ul.setValue(0)

        self.entry_flowrate_ul_per_s = QDoubleSpinBox()
        self.entry_flowrate_ul_per_s.setMinimum(0) 
        self.entry_flowrate_ul_per_s.setMaximum(20) 
        self.entry_flowrate_ul_per_s.setSingleStep(0.1)
        self.entry_flowrate_ul_per_s.setValue(0)

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