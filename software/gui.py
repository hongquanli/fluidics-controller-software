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

		# layout widgets
		layout = QGridLayout()
		layout.addWidget(self.chillerWidger,0,0)
		layout.addWidget(self.preUseCheckWidget,1,0)
		layout.addWidget(self.sequenceWidget,4,0)
		# layout.addWidget(self.triggerWidget,8,0)
		layout.addWidget(self.manualFlushWidget,9,0)
		layout.addWidget(self.logWidget,10,0)

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