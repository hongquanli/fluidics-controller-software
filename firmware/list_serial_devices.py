import serial
import serial.tools.list_ports
for p in serial.tools.list_ports.comports():
	# print(p.description)
	# print(p)
	print(p.__dict__)
