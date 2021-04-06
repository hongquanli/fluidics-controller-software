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
		self.fluidController = controllers.FluidController_simulation()
		self.logger = controllers.Logger()

		# load widgets
		self.chillerWidger = widgets.ChillerWidget(self.fluidController)
		self.preUseCheckWidget = widgets.PreUseCheckWidget(self.fluidController)
		self.logWidget = QListWidget()
		# self.triggerWidget = widgets.TriggerWidget(self.triggerController)
		self.sequenceWidget = widgets.SequenceWidget(self.fluidController)
		self.manualFlushWidget = widgets.ManualFlushWidget(self.fluidController)

		# layout widgets (linear)
		'''
		layout = QGridLayout()
		layout.addWidget(QLabel('Chiller'),0,0)
		layout.addWidget(self.chillerWidger,0,1)
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
		tab1_layout.addWidget(QLabel('Chiller'),0,0)
		tab1_layout.addWidget(self.chillerWidger,0,1)
		tab1_layout.addWidget(QLabel('Pre-Use Check'),1,0)
		tab1_layout.addWidget(self.preUseCheckWidget,1,1)
		tab1_layout.addWidget(QLabel('Sequences'),4,0)
		tab1_layout.addWidget(self.sequenceWidget,4,1)
		tab1_widget = QWidget()
		
		tab1_widget.setLayout(tab1_layout)
		tab2_widget = QWidget()

		tabWidget = QTabWidget()
		tabWidget.addTab(tab1_widget, "Run Experiments")
		tabWidget.addTab(tab2_widget, "Manual Control")

		layout = QGridLayout()
		layout.addWidget(tabWidget,0,0)
		# layout.addWidget(self.logWidget,1,0)
		# @@@ the code below is to put the ListWidget into a frame - code to be improved -  well it doesn't work
		#self.framedLogWidget = QFrame()
		#framedLogWidget_layout = QHBoxLayout() 
		#framedLogWidget_layout.addWidget(self.logWidget)
		#framedLogWidget_layout.addWidget(QLabel('test')
		#self.framedLogWidget.setLayout(framedLogWidget_layout)
		#layout.addWidget(self.framedLogWidget,1,0)
		layout.addWidget(self.logWidget,1,0)
		# layout widgets (using tabs)  - end

		# connecting signals to slots
		self.chillerWidger.log_message.connect(self.logWidget.addItem)
		self.preUseCheckWidget.log_message.connect(self.logWidget.addItem)
		self.fluidController.log_message.connect(self.logWidget.addItem)
		# self.triggerController.log_message.connect(self.logWidget.addItem)
		self.sequenceWidget.log_message.connect(self.logWidget.addItem)
		self.manualFlushWidget.log_message.connect(self.logWidget.addItem)

		self.chillerWidger.log_message.connect(self.logWidget.scrollToBottom)
		self.preUseCheckWidget.log_message.connect(self.logWidget.scrollToBottom)
		self.fluidController.log_message.connect(self.logWidget.scrollToBottom)
		# self.triggerController.log_message.connect(self.logWidget.scrollToBottom)
		self.sequenceWidget.log_message.connect(self.logWidget.scrollToBottom)
		self.manualFlushWidget.log_message.connect(self.logWidget.scrollToBottom)
		
		self.chillerWidger.log_message.connect(self.logger.log)
		self.preUseCheckWidget.log_message.connect(self.logger.log)
		self.fluidController.log_message.connect(self.logger.log)
		# self.triggerController.log_message.connect(self.logger.log)
		self.sequenceWidget.log_message.connect(self.logger.log)
		self.manualFlushWidget.log_message.connect(self.logger.log)
		
		# transfer the layout to the central widget
		self.centralWidget = QWidget()
		self.centralWidget.setLayout(layout)
		self.setCentralWidget(self.centralWidget)

	def closeEvent(self, event):
		event.accept()