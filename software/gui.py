# set QT_API environment variable
import os 
os.environ["QT_API"] = "pyqt5"
import qtpy

# qt libraries
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from qtpy.QtGui import *

# app specific libraries
import controllers
import widgets

class STARmapAutomationControllerGUI(QMainWindow):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# load objects
		# self.triggerController = controllers.TriggerController()
		# self.triggerController = controllers.TriggerController_simulation()
		#elf.fluidController = controllers.FluidController()

		self.teensy41 = controllers.Microcontroller()
		# self.teensy41 = controllers.Microcontroller_Simulation()
		self.fluidController = controllers.FluidController(self.teensy41)
		self.logger = controllers.Logger()

		# load widgets
		self.chillerWidget = widgets.ChillerWidget(self.fluidController)
		self.preUseCheckWidget = widgets.PreUseCheckWidget(self.fluidController)
		self.logWidget = QListWidget()
		# self.triggerWidget = widgets.TriggerWidget(self.triggerController)
		self.sequenceWidget = widgets.SequenceWidget(self.fluidController)
		self.manualFlushWidget = widgets.ManualFlushWidget(self.fluidController)
		self.microcontrollerStateDisplayWidget = widgets.MicrocontrollerStateDisplayWidget()

		# layout widgets (linear)
		'''
		layout = QGridLayout()
		layout.addWidget(QLabel('Chiller'),0,0)
		layout.addWidget(self.chillerWidget,0,1)
		layout.addWidget(QLabel('Pre-Use Check'),1,0)
		layout.addWidget(self.preUseCheckWidget,1,1)
		layout.addWidget(QLabel('Sequences'),4,0)
		layout.addWidget(self.sequenceWidget,4,1)
		# layout.addWidget(self.triggerWidget,8,0)
		layout.addWidget(QLabel('Manual Flush'),9,0) # (End of Experiment)
		layout.addWidget(self.manualFlushWidget,9,1)
		layout.addWidget(self.logWidget,10,0,1,2)
		'''

		# layout widgets (using tabs)  - start
		tab1_layout = QGridLayout()
		# tab1_layout.addWidget(QLabel('Chiller'),0,0)
		# tab1_layout.addWidget(self.chillerWidget,0,1)
		tab1_layout.addWidget(QLabel('Pre-Use Check'),1,0)
		tab1_layout.addWidget(self.preUseCheckWidget,1,1)
		tab1_layout.addWidget(QLabel('Sequences'),4,0)
		tab1_layout.addWidget(self.sequenceWidget,4,1)
		tab1_widget = QWidget()
		
		tab1_widget.setLayout(tab1_layout)
		tab2_widget = QWidget()

		self.tabWidget = QTabWidget()
		self.tabWidget.addTab(tab1_widget, "Run Experiments")
		self.tabWidget.addTab(tab2_widget, "Manual Control")
		
		layout = QGridLayout()
		layout.addWidget(self.tabWidget,0,0)

		# layout.addWidget(self.logWidget,1,0)
		# @@@ the code below is to put the ListWidget into a frame - code may be improved
		self.framedLogWidget = QFrame()
		framedLogWidget_layout = QHBoxLayout() 
		framedLogWidget_layout.addWidget(self.logWidget)
		self.framedLogWidget.setLayout(framedLogWidget_layout)
		self.framedLogWidget.setFrameStyle(QFrame.Panel | QFrame.Raised)
		'''
		mcuStateDisplay = QGridLayout()
		mcuStateDisplay.addWidget(QLabel('Controller State'),0,0)
		mcuStateDisplay.addWidget(self.microcontrollerStateDisplayWidget,0,1)
		layout.addLayout(mcuStateDisplay,1,0)
		'''
		layout.addWidget(self.microcontrollerStateDisplayWidget,1,0)
		layout.addWidget(self.framedLogWidget,2,0)
		# layout widgets (using tabs)  - end

		# connecting signals to slots
		# @@@ to do: addItem and scrollToBottom need to happen in sequence - create a function for this
		self.chillerWidget.log_message.connect(self.logWidget.addItem)
		self.preUseCheckWidget.log_message.connect(self.logWidget.addItem)
		self.fluidController.log_message.connect(self.logWidget.addItem)
		# self.triggerController.log_message.connect(self.logWidget.addItem)
		self.sequenceWidget.log_message.connect(self.logWidget.addItem)
		self.manualFlushWidget.log_message.connect(self.logWidget.addItem)

		self.chillerWidget.log_message.connect(self.logWidget.scrollToBottom)
		self.preUseCheckWidget.log_message.connect(self.logWidget.scrollToBottom)
		self.fluidController.log_message.connect(self.logWidget.scrollToBottom)
		# self.triggerController.log_message.connect(self.logWidget.scrollToBottom)
		self.sequenceWidget.log_message.connect(self.logWidget.scrollToBottom)
		self.manualFlushWidget.log_message.connect(self.logWidget.scrollToBottom)
		
		self.chillerWidget.log_message.connect(self.logger.log)
		self.preUseCheckWidget.log_message.connect(self.logger.log)
		self.fluidController.log_message.connect(self.logger.log)
		# self.triggerController.log_message.connect(self.logger.log)
		self.sequenceWidget.log_message.connect(self.logger.log)
		self.manualFlushWidget.log_message.connect(self.logger.log)

		self.sequenceWidget.signal_disable_manualControlWidget.connect(self.disableManualControlWidget)
		self.sequenceWidget.signal_enable_manualControlWidget.connect(self.enableManualControlWidget)

		self.fluidController.signal_initialize_stopwatch_display.connect(self.logWidget.addItem)
		self.fluidController.signal_initialize_stopwatch_display.connect(self.logWidget.scrollToBottom)
		self.fluidController.signal_update_stopwatch_display.connect(self.update_stopwatch_display)

		# connections for displaying the MCU state
		self.fluidController.signal_MCU_CMD_UID.connect(self.microcontrollerStateDisplayWidget.label_MCU_CMD_UID.setNum)
		self.fluidController.signal_pump_power.connect(self.microcontrollerStateDisplayWidget.label_pump_power.setText)
		self.fluidController.signal_selector_valve_position.connect(self.microcontrollerStateDisplayWidget.label_selector_valve_position.setNum)
		self.fluidController.signal_pressure.connect(self.microcontrollerStateDisplayWidget.label_pressure.setText)
		self.fluidController.signal_vacuum.connect(self.microcontrollerStateDisplayWidget.label_vacuum.setText)

		
		# transfer the layout to the central widget
		self.centralWidget = QWidget()
		self.centralWidget.setLayout(layout)
		self.setCentralWidget(self.centralWidget)

	def disableManualControlWidget(self):
		self.tabWidget.setTabEnabled(1,False)

	def enableManualControlWidget(self):
		self.tabWidget.setTabEnabled(1,True)

	def update_stopwatch_display(self,text):
		if 'stop watch remaining time' in self.logWidget.item(self.logWidget.count()-1).text():
			# use this if statement to prevent other messages being overwritten
			self.logWidget.item(self.logWidget.count()-1).setText(text)

	def closeEvent(self, event):
		event.accept()