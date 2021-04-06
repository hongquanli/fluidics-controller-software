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
        # hbox.addWidget(QLabel('[Pre-use Check]]'))
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
        self.attributes['Sequence'] = QLabel(self.sequence_name)
        self.attributes['Fluidic Port'] = QSpinBox()
        self.attributes['Fluidic Port'].setMinimum(1) # 0: virtual port - does not care
        self.attributes['Fluidic Port'].setMaximum(24)
        self.attributes['Flow Time (s)'] = QDoubleSpinBox()
        self.attributes['Flow Time (s)'].setMinimum(0) # -1: no flow
        self.attributes['Flow Time (s)'].setMaximum(FLOW_TIME_MAX) 
        self.attributes['Incubation Time (min)'] = QDoubleSpinBox()
        self.attributes['Incubation Time (min)'].setMinimum(0) # -1: no incubation
        self.attributes['Incubation Time (min)'].setMaximum(INCUBATION_TIME_MAX_MIN)
        self.attributes['Repeat'] = QSpinBox()
        self.attributes['Repeat'].setMinimum(1)
        self.attributes['Repeat'].setMaximum(5)
        self.attributes['Include'] = QCheckBox()
        # manually make sure the keys are included in SEQUENCE_ATTRIBUTES_KEYS
        
class SequenceWidget(QFrame):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.abort_requested = False
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):

        tableWidget = QTableWidget(len(SEQUENCE_NAME),len(SEQUENCE_ATTRIBUTES_KEYS),self)
        tableWidget.setHorizontalHeaderLabels(SEQUENCE_ATTRIBUTES_KEYS)
        
        # create the sequences, set the attributes and add the sequences into the tabel
        self.sequences = {}
        for i in range(len(SEQUENCE_NAME)):
            sequence_name = SEQUENCE_NAME[i]
            self.sequences[sequence_name] = SequenceEntry(sequence_name)
            # insert attributes of the current sequence into the table
            for j in range(len(SEQUENCE_ATTRIBUTES_KEYS)):
                attribute_key = SEQUENCE_ATTRIBUTES_KEYS[j]
                tableWidget.setCellWidget(i,j,self.sequences[sequence_name].attributes[attribute_key])
            # tableWidget.setCellWidget(i,0,self.sequences[sequence_name].attributes['Label'])

        # set sequence-specific attributes
        self.sequences['Add Imaging Buffer'].attributes['Incubation Time (min)'].setMinimum(-1)
        self.sequences['Add Imaging Buffer'].attributes['Incubation Time (min)'].setValue(-1)
        self.sequences['Remove Imaging Buffer'].attributes['Flow Time (s)'].setMinimum(-1)
        self.sequences['Remove Imaging Buffer'].attributes['Flow Time (s)'].setValue(-1)
        self.sequences['Stain with DAPI'].attributes['Incubation Time (min)'].setMinimum(-1)
        self.sequences['Stain with DAPI'].attributes['Incubation Time (min)'].setValue(-1)
        self.sequences['Add Imaging Buffer'].attributes['Incubation Time (min)'].setEnabled(False)
        self.sequences['Remove Imaging Buffer'].attributes['Flow Time (s)'].setEnabled(False)
        self.sequences['Stain with DAPI'].attributes['Incubation Time (min)'].setEnabled(False)
        self.sequences['Ligate'].attributes['Repeat'].setEnabled(False)
        self.sequences['Add Imaging Buffer'].attributes['Repeat'].setEnabled(False)
        self.sequences['Remove Imaging Buffer'].attributes['Repeat'].setEnabled(False)
        self.sequences['Remove Imaging Buffer'].attributes['Incubation Time (min)'].setEnabled(False)
        self.sequences['Stain with DAPI'].attributes['Repeat'].setEnabled(False)
        self.sequences['Remove Imaging Buffer'].attributes['Fluidic Port'].setMinimum(0)
        self.sequences['Remove Imaging Buffer'].attributes['Fluidic Port'].setValue(0)
        self.sequences['Remove Imaging Buffer'].attributes['Fluidic Port'].setEnabled(False)

        '''
        # changed to disable instead of no buttons
        self.sequences['Ligate'].attributes['Repeat'].setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.sequences['Add Imaging Buffer'].attributes['Repeat'].setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.sequences['Remove Imaging Buffer'].attributes['Repeat'].setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.sequences['Stain with DAPI'].attributes['Repeat'].setButtonSymbols(QAbstractSpinBox.NoButtons)
        '''

        # (temporary) set sequence-specific attributes - to do: load from file
        self.sequences['Strip'].attributes['Repeat'].setValue(2)
        self.sequences['Strip'].attributes['Incubation Time (min)'].setValue(600/60)
        self.sequences['Wash (Post-Strip)'].attributes['Repeat'].setValue(3)
        self.sequences['Wash (Post-Strip)'].attributes['Incubation Time (min)'].setValue(300/60)
        self.sequences['Ligate'].attributes['Incubation Time (min)'].setValue(3600*3/60)
        self.sequences['Wash (Post-Ligation)'].attributes['Repeat'].setValue(3)
        self.sequences['Wash (Post-Ligation)'].attributes['Incubation Time (min)'].setValue(600/60)

        # (temporary) port mapping - to be done through _def.py
        self.sequences['Strip'].attributes['Fluidic Port'].setValue(10)
        self.sequences['Strip'].attributes['Fluidic Port'].setEnabled(False)
        self.sequences['Wash (Post-Strip)'].attributes['Fluidic Port'].setValue(8)
        self.sequences['Wash (Post-Strip)'].attributes['Fluidic Port'].setEnabled(False)
        self.sequences['Wash (Post-Ligation)'].attributes['Fluidic Port'].setValue(9)
        self.sequences['Wash (Post-Ligation)'].attributes['Fluidic Port'].setEnabled(False)
        self.sequences['Add Imaging Buffer'].attributes['Fluidic Port'].setValue(9)
        self.sequences['Add Imaging Buffer'].attributes['Fluidic Port'].setEnabled(False)
        self.sequences['Stain with DAPI'].attributes['Fluidic Port'].setValue(6)
        self.sequences['Stain with DAPI'].attributes['Fluidic Port'].setEnabled(False)
        self.sequences['Ligate'].attributes['Fluidic Port'].setMaximum(4)

        # set table size
        tableWidget.resizeColumnsToContents()
        tableWidget.setFixedSize(tableWidget.horizontalHeader().length() + 
                   tableWidget.verticalHeader().width(),tableWidget.verticalHeader().length() + 
                   tableWidget.horizontalHeader().height())

        # button
        self.button_save = QPushButton('Save Sequence Setttings')
        self.button_load = QPushButton('Load Sequence Setttings')
        self.button_run = QPushButton('Run Selected Sequences')
        self.button_stop = QPushButton('Abort')

        vbox = QVBoxLayout()
        vbox.addWidget(tableWidget)
        grid_btns = QGridLayout()
        # grid_btns.addWidget(self.button_run,0,0,1,2)
        grid_btns.addWidget(self.button_save,0,0)
        grid_btns.addWidget(self.button_load,0,1)
        # grid_btns.addWidget(self.button_run,1,0,1,2)
        grid_btns.addWidget(self.button_run,1,0)
        grid_btns.addWidget(self.button_stop,1,1)
        vbox.addLayout(grid_btns)
        self.setLayout(vbox)

        # make connections
        self.button_run.clicked.connect(self.run_sequences)
        self.button_stop.clicked.connect(self.stop_sequence)
        #self.button_stop.setEnabled(False) # the current implementation of run_sequences is blocking, yet abort is possible through a flag in FluidController. Actually the flag can be in the widget. Maybe use in both places, so that for example, wait can be aborted
        self.button_save.setEnabled(False) # saving settings to be implemented, disable the button for now
        self.button_load.setEnabled(False) # loading settings to be implemented, disable the button for now

    def run_sequences(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Confirm your action")
        msg.setInformativeText("Click OK to run the selected sequences")
        msg.setWindowTitle("Confirmation")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)

        retval = msg.exec_()
        if QMessageBox.Ok == retval:
            self.abort_requested = False
            # go through sequences and execute *selected* sequences
            for i in range(len(SEQUENCE_NAME)):
                current_sequence = self.sequences[SEQUENCE_NAME[i]]
                if current_sequence.attributes['Include'].isChecked() == True:
                    for k in range(current_sequence.attributes['Repeat'].value()):
                        if self.abort_requested == False:
                            self.log_message.emit(utils.timestamp() + 'Execute ' + SEQUENCE_NAME[i] + ', round ' + str(k+1))
                            QApplication.processEvents()
                            # let the backend fluidController execute the sequence
                            self.fluidController.run_sequence(SEQUENCE_NAME[i],
                                current_sequence.attributes['Flow Time (s)'].value(),
                                current_sequence.attributes['Incubation Time (min)'].value())
                        else:
                            self.log_message.emit(utils.timestamp() + '! ' + SEQUENCE_NAME[i] + ', round ' + str(k+1) + ' aborted')
                            QApplication.processEvents()
        else:
            self.log_message.emit(utils.timestamp() + 'no action.')
            QApplication.processEvents()

    def stop_sequence(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Confirm your action")
        msg.setInformativeText("Click Abort to stop advancing to the next sequence")
        msg.setWindowTitle("Confirmation")
        msg.setStandardButtons(QMessageBox.Abort | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)
        retval = msg.exec_()
        if QMessageBox.Abort == retval:
            self.abort_requested = True
            self.fluidController.request_abort_sequences()
            self.log_message.emit(utils.timestamp() + 'Abort requested')
            QApplication.processEvents()
        else:
            pass


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
        # hbox.addWidget(QLabel('[Manual Bleach]'))
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
        # hbox.addWidget(QLabel('[Chiller]'))
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