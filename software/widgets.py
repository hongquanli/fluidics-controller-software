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
    signal_disable_manualControlWidget = Signal()
    signal_enable_manualControlWidget = Signal()

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.abort_requested = False
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):

        self.tableWidget = QTableWidget(len(SEQUENCE_NAME),len(SEQUENCE_ATTRIBUTES_KEYS),self)
        self.tableWidget.setHorizontalHeaderLabels(SEQUENCE_ATTRIBUTES_KEYS)
        
        # create the sequences, set the attributes and add the sequences into the tabel
        self.sequences = {}
        for i in range(len(SEQUENCE_NAME)):
            sequence_name = SEQUENCE_NAME[i]
            self.sequences[sequence_name] = SequenceEntry(sequence_name)
            # insert attributes of the current sequence into the table
            for j in range(len(SEQUENCE_ATTRIBUTES_KEYS)):
                attribute_key = SEQUENCE_ATTRIBUTES_KEYS[j]
                self.tableWidget.setCellWidget(i,j,self.sequences[sequence_name].attributes[attribute_key])
            # self.tableWidget.setCellWidget(i,0,self.sequences[sequence_name].attributes['Label'])

        # set sequence-specific attributes
        self.sequences['Add Imaging Buffer'].attributes['Incubation Time (min)'].setMinimum(-1)
        self.sequences['Add Imaging Buffer'].attributes['Incubation Time (min)'].setValue(-1)
        self.sequences['Remove Medium'].attributes['Flow Time (s)'].setMinimum(-1) 
        self.sequences['Remove Medium'].attributes['Flow Time (s)'].setValue(-1)
        # self.sequences['Remove Medium'].attributes['Flow Time (s)'].setMinimum(0)       # *** for now, use fixed aspiration time instead of bubble sensor (waiting for the sensor with the right tubing ID to arrive) ***
        # self.sequences['Remove Medium'].attributes['Flow Time (s)'].setValue(20)        # *** for now, use fixed aspiration time instead of bubble sensor (waiting for the sensor with the right tubing ID to arrive) ***
        self.sequences['Stain with DAPI'].attributes['Incubation Time (min)'].setMinimum(-1)
        self.sequences['Stain with DAPI'].attributes['Incubation Time (min)'].setValue(-1)

        self.sequences['Add Imaging Buffer'].attributes['Incubation Time (min)'].setEnabled(False)
        self.sequences['Remove Medium'].attributes['Flow Time (s)'].setEnabled(False) 
        # self.sequences['Remove Medium'].attributes['Flow Time (s)'].setEnabled(True)    # *** for now, use fixed aspiration time instead of bubble sensor (waiting for the sensor with the right tubing ID to arrive) ***
        self.sequences['Stain with DAPI'].attributes['Incubation Time (min)'].setEnabled(False)
        self.sequences['Ligate'].attributes['Repeat'].setEnabled(False)
        self.sequences['Add Imaging Buffer'].attributes['Repeat'].setEnabled(False)
        self.sequences['Remove Medium'].attributes['Repeat'].setEnabled(False)
        self.sequences['Remove Medium'].attributes['Incubation Time (min)'].setEnabled(False)
        self.sequences['Stain with DAPI'].attributes['Repeat'].setEnabled(False)
        self.sequences['Remove Medium'].attributes['Fluidic Port'].setMinimum(0)
        self.sequences['Remove Medium'].attributes['Fluidic Port'].setValue(0)
        self.sequences['Remove Medium'].attributes['Fluidic Port'].setEnabled(False)

        '''
        # changed to disable instead of no buttons
        self.sequences['Ligate'].attributes['Repeat'].setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.sequences['Add Imaging Buffer'].attributes['Repeat'].setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.sequences['Remove Medium'].attributes['Repeat'].setButtonSymbols(QAbstractSpinBox.NoButtons)
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

        # set table size - reference: https://stackoverflow.com/questions/8766633/how-to-determine-the-correct-size-of-a-qtablewidget
        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.setFixedSize(self.tableWidget.horizontalHeader().length() + 
                   self.tableWidget.verticalHeader().width(),self.tableWidget.verticalHeader().length() + 
                   self.tableWidget.horizontalHeader().height())
        self.tableWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tableWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # settings loading and saveing
        self.lineEdit_setting_file = QLineEdit()
        self.lineEdit_setting_file.setReadOnly(True)
        self.lineEdit_setting_file.setText('[ Click Browse to Select a Setting File ]')
        self.btn_select_setting_file = QPushButton('Browse')
        self.btn_select_setting_file.setDefault(False)
        self.btn_select_setting_file.setIcon(QIcon('icon/folder.png'))

        # button
        self.button_save = QPushButton('Save Sequence Setttings')
        self.button_load = QPushButton('Load Sequence Setttings')
        self.button_run = QPushButton('Run Selected Sequences')
        self.button_stop = QPushButton('Abort')

        vbox = QVBoxLayout()
        vbox.addWidget(self.tableWidget)
        hbox_settings_loading_and_saving = QHBoxLayout()
        hbox_settings_loading_and_saving.addWidget(self.lineEdit_setting_file)
        hbox_settings_loading_and_saving.addWidget(self.btn_select_setting_file)
        hbox_settings_loading_and_saving.addWidget(self.button_load)
        hbox_settings_loading_and_saving.addWidget(self.button_save)
        vbox.addLayout(hbox_settings_loading_and_saving)
        grid_btns = QGridLayout()
        # grid_btns.addWidget(self.button_save,0,0)
        # grid_btns.addWidget(self.button_load,0,1)
        grid_btns.addWidget(self.button_run,1,0)
        grid_btns.addWidget(self.button_stop,1,1)
        vbox.addLayout(grid_btns)
        self.setLayout(vbox)

        # make connections
        self.button_run.clicked.connect(self.run_sequences)
        self.button_stop.clicked.connect(self.request_to_abort_sequences)
        # @@@ need to make sure button_stop is still clickable while self.run_sequences() is being executed - done [4/7/2021]
        self.button_stop.setEnabled(False) # the current implementation of run_sequences is blocking, yet abort is possible through a flag in FluidController. Actually the flag can be in the widget. Maybe use in both places, so that for example, wait can be aborted [addressed 4/7/2021]
        self.button_save.setEnabled(False) # saving settings to be implemented, disable the button for now
        self.button_load.setEnabled(False) # loading settings to be implemented, disable the button for now
        self.fluidController.signal_sequences_execution_stopped.connect(self.enable_widgets_except_for_abort_btn)

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
            self.disable_widgets_except_for_abort_btn() 
            # print a seperator for visuals
            self.log_message.emit('--------------------------------')
            # go through sequences and execute *selected* sequences
            for i in range(len(SEQUENCE_NAME)):
                current_sequence = self.sequences[SEQUENCE_NAME[i]]
                if current_sequence.attributes['Include'].isChecked() == True:
                    for k in range(current_sequence.attributes['Repeat'].value()):
                        self.log_message.emit(utils.timestamp() + 'Add ' + SEQUENCE_NAME[i] + ', round ' + str(k+1) + ' to the queue')
                        QApplication.processEvents()
                        ################################################################
                        ##### let the backend fluidController execute the sequence #####
                        ################################################################
                        self.fluidController.add_sequence(
                            SEQUENCE_NAME[i],
                            current_sequence.attributes['Fluidic Port'].value(),
                            current_sequence.attributes['Flow Time (s)'].value(),
                            current_sequence.attributes['Incubation Time (min)'].value(),
                            pressure_setting=None,
                            round_ = k)
            self.fluidController.start_sequence_execution()

            # self.signal_enable_manualControlWidget.emit()
        else:
            self.log_message.emit(utils.timestamp() + 'no action.')
            QApplication.processEvents()

    def request_to_abort_sequences(self):
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

    def disable_widgets_except_for_abort_btn(self):
        self.signal_disable_manualControlWidget.emit()
        self.tableWidget.setEnabled(False)
        self.lineEdit_setting_file.setEnabled(False)
        self.btn_select_setting_file.setEnabled(False)
        # self.button_load.setEnabled(False)
        # self.button_save.setEnabled(False)
        self.button_run.setEnabled(False)
        self.button_stop.setEnabled(True)
        QApplication.processEvents()

    def enable_widgets_except_for_abort_btn(self):
        self.tableWidget.setEnabled(True)
        self.lineEdit_setting_file.setEnabled(True)
        self.btn_select_setting_file.setEnabled(True)
        # self.button_load.setEnabled(True)
        # self.button_save.setEnabled(True)
        self.button_run.setEnabled(True)
        self.button_stop.setEnabled(False)
        self.signal_enable_manualControlWidget.emit()
        QApplication.processEvents()


'''
#########################################################
#########   MCU -> Computer message structure   #########
#########################################################
byte 0-1    : computer -> MCU CMD counter (UID)
byte 2      : cmd from host computer (error checking through check sum => no need to transmit back the parameters associated with the command)
            <see below for command set>
byte 3      : status of the command
                - 1: in progress
                - 0: completed without errors
                - 2: error in cmd check sum
                - 3: invalid cmd
                - 4: error during execution
byte 4      : MCU internal program being executed
                - 0: idle
                <see below for command set>
byte 5      : state of valve A1,A2,B1,B2,bubble_sensor_1,bubble_sensor_2,x,x
byte 6      : state of valve C1-C7, manual input bit
byte 7-8    : pump power
byte 9-10   : pressure sensor 1 reading
byte 11-12  : pressure sensor 2 reading
byte 13-14  : flow sensor 1 reading
byte 15-16  : flow sensor 2 reading
byte 17-19  : reserved
'''

class MicrocontrollerStateDisplayWidget(QFrame):
    def __init__(self, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_components()
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):
        self.label_MCU_CMD_UID = QLabel()
        self.label_CMD = QLabel()
        self.label_CMD_status = QLabel()
        self.label_MCU_internal_program = QLabel()
        self.label_pump_power = QLabel()
        self.label_selector_valve_position = QLabel()
        self.label_pressure = QLabel()
        self.label_vacuum = QLabel()
        self.label_bubble_sensor_upstream = QLabel()
        self.label_bubble_sensor_downstream = QLabel()

        self.label_MCU_CMD_UID.setFixedWidth(50)
        self.label_CMD.setFixedWidth(30)
        self.label_CMD_status.setFixedWidth(50)
        self.label_MCU_internal_program.setFixedWidth(130)
        self.label_pump_power.setFixedWidth(50)
        self.label_selector_valve_position.setFixedWidth(30)
        self.label_pressure.setFixedWidth(50)
        self.label_vacuum.setFixedWidth(50)

        self.label_MCU_CMD_UID.setFrameStyle(QFrame.Panel | QFrame.Sunken)        
        self.label_CMD.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.label_CMD_status.setFrameStyle(QFrame.Panel | QFrame.Sunken)        
        self.label_MCU_internal_program.setFrameStyle(QFrame.Panel | QFrame.Sunken)        
        self.label_pump_power.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.label_selector_valve_position.setFrameStyle(QFrame.Panel | QFrame.Sunken)        
        self.label_pressure.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.label_vacuum.setFrameStyle(QFrame.Panel | QFrame.Sunken)        
        self.label_bubble_sensor_upstream.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.label_bubble_sensor_downstream.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()
        # hbox3 = QHBoxLayout()
        hbox4 = QHBoxLayout()

        tmp = QLabel('CMD UID')
        tmp.setFixedWidth(80)
        hbox1.addWidget(tmp)
        hbox1.addWidget(self.label_MCU_CMD_UID)

        tmp = QLabel('CMD')
        tmp.setFixedWidth(100)
        hbox1.addWidget(tmp)
        hbox1.addWidget(self.label_CMD)

        tmp = QLabel('CMD Status')
        tmp.setFixedWidth(80)
        hbox1.addWidget(tmp)
        hbox1.addWidget(self.label_CMD_status)

        hbox1.addWidget(QLabel('MCU Internal Program'))
        hbox1.addWidget(self.label_MCU_internal_program)
        hbox1.addStretch()

        tmp = QLabel('Pump Power')
        tmp.setFixedWidth(80)
        hbox2.addWidget(tmp)
        hbox2.addWidget(self.label_pump_power)

        tmp = QLabel('Rotary Valve Pos')
        tmp.setFixedWidth(100)
        hbox2.addWidget(tmp)
        hbox2.addWidget(self.label_selector_valve_position)
        #hbox2.addStretch()

        tmp = QLabel('Pressure (psi)')
        tmp.setFixedWidth(80)
        hbox2.addWidget(tmp)
        hbox2.addWidget(self.label_pressure)

        tmp = QLabel('Vacuum (psi)')
        tmp.setFixedWidth(80)
        hbox2.addWidget(tmp)
        hbox2.addWidget(self.label_vacuum)
        hbox2.addWidget(QLabel('Bubble Sensor (in)'))
        hbox2.addWidget(self.label_bubble_sensor_upstream) # 0 - liquid present
        hbox2.addWidget(QLabel('Bubble Sensor (out)'))
        hbox2.addWidget(self.label_bubble_sensor_downstream) # 0 - liquid present
        hbox2.addStretch()

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox4)
        self.setLayout(vbox)


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


class ManualControlWidget(QWidget):

    log_message = Signal(str)

    def __init__(self, fluidController, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fluidController = fluidController
        self.add_components()
        # self.setFrameStyle(QFrame.Panel | QFrame.Raised)

    def add_components(self):

        # self.entry_selector_valve_position = QSpinBox()
        # self.entry_selector_valve_position.setMinimum(1)
        # self.entry_selector_valve_position.setMaximum(24)
        # self.entry_selector_valve_position.setFixedWidth(40)

        self.dropdown_selector_valve_position = QComboBox()
        for i in range(24):
            self.dropdown_selector_valve_position.addItem(str(i+1))
        self.dropdown_selector_valve_position.setFixedWidth(70)

        # self.entry_10mm_solenoid_valve_selection = QSpinBox()
        # self.entry_10mm_solenoid_valve_selection.setMinimum(0)
        # self.entry_10mm_solenoid_valve_selection.setMaximum(16)
        # self.entry_10mm_solenoid_valve_selection.setFixedWidth(40)

        self.dropdown_10mm_solenoid_valve_selection = QComboBox()
        for i in range(17):
            self.dropdown_10mm_solenoid_valve_selection.addItem(str(i))
        self.dropdown_10mm_solenoid_valve_selection.setFixedWidth(70)

        hbox1 = QHBoxLayout()
        tmp = QLabel('Set Selector Valve Position To')
        tmp.setFixedWidth(190)
        hbox1.addWidget(tmp)
        hbox1.addWidget(self.dropdown_selector_valve_position)
        hbox1.addStretch()

        hbox2 = QHBoxLayout()
        tmp = QLabel('Turn On 10mm Solenoid Valve #')
        tmp.setFixedWidth(190)
        hbox2.addWidget(tmp)
        hbox2.addWidget(self.dropdown_10mm_solenoid_valve_selection)
        hbox2.addWidget(QLabel('(select 1-16 to turn on one of the valves, enter 0 to turn off all the valves)'))
        hbox2.addStretch()

        framedHbox1 = frameWidget(hbox1)
        framedHbox2 = frameWidget(hbox2)

        vbox = QVBoxLayout()
        vbox.addWidget(framedHbox1)
        vbox.addWidget(framedHbox2)
        vbox.addStretch()

        self.setLayout(vbox)

        self.dropdown_selector_valve_position.currentTextChanged.connect(self.update_selector_valve)
        self.dropdown_10mm_solenoid_valve_selection.currentTextChanged.connect(self.update_10mm_solenoid_valves)

    def update_selector_valve(self,pos_str):
        self.fluidController.add_sequence('Set Selector Valve Position',int(pos_str))
        self.fluidController.start_sequence_execution()

    def update_10mm_solenoid_valves(self,pos_str):
        self.fluidController.add_sequence('Set 10 mm Valve State',int(pos_str))
        self.fluidController.start_sequence_execution()

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


class frameWidget(QFrame):

    def __init__(self, layout, main=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setLayout(layout)