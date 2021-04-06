Ports_Name = ['1','2','3','4','Air (5)','DAPI (6)','Nissl (7)','Wash Buffer (8)','Imaging Buffer (9)','Strip Buffer (10)']
Ports_Number = 	[1,2,3,4,5,6,7,8,9,10]

INCUBATION_TIME_MAX_MIN = 3600*3/60
FLOW_TIME_MAX = 60

SEQUENCE_ATTRIBUTES_KEYS = ['Sequence','Fluidic Port','Flow Time (s)','Incubation Time (min)','Repeat','Include']
SEQUENCE_NAME = ['Strip','Wash (Post-Strip)','Ligate','Wash (Post-Ligation)','Add Imaging Buffer','Remove Imaging Buffer','Stain with DAPI']

# sequences
'''
1. strip - volume (time) [1.2 ml] - wait time - number of times [2]
2. wash (post-strip) - volume (time) [1.2 ml] - wait time - number of cycles [3]
3. sequencing mixture - all available - wait time
4. wash (post ligation) - volume (time) - wait time - number of cycles [3]
4. imaging buffer - volume (time) [1.2 ml]
5. DAPI - volume (time) [1.2 ml] - wait time
'''