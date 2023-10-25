from lxml import etree as ET
import pandas as pd
top = ET.Element('settings')

def generate_default_configuration(filename):

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Remove Medium')
    sequence.set('Fluidic_Port', '0')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','-1')
    sequence.set('Flow_Time_in_second','-1')
    sequence.set('Post_Fill_Fluidic_Port', '0')
    
    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Stripping Buffer Wash')
    sequence.set('Fluidic_Port', '7')
    sequence.set('Repeat','2')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')
    sequence.set('Post_Fill_Fluidic_Port', '0')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Rendering Buffer Wash')
    sequence.set('Fluidic_Port', '8')
    sequence.set('Repeat','3')
    sequence.set('Incubation_Time_in_minute','5')
    sequence.set('Flow_Time_in_second','15')
    sequence.set('Post_Fill_Fluidic_Port', '0')
    
    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Hybridize')
    sequence.set('Fluidic_Port', '1')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','180')
    sequence.set('Flow_Time_in_second','15')
    sequence.set('Post_Fill_Fluidic_Port', '0')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Rendering Buffer Wash 2')
    sequence.set('Fluidic_Port', '1')
    sequence.set('Repeat','2')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Imaging Buffer Wash')
    sequence.set('Fluidic_Port', '9')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')
    sequence.set('Post_Fill_Fluidic_Port', '0')
    
    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Add Imaging Buffer')
    sequence.set('Fluidic_Port', '9')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','-1')
    sequence.set('Flow_Time_in_second','0')
    sequence.set('Post_Fill_Fluidic_Port', '0')
    
    setting = ET.SubElement(top,'aspiration_setting')
    setting.set('Pump_Power','0.4')
    setting.set('Duration_Seconds','8')

    tree = ET.ElementTree(top)
    tree.write(filename,encoding="utf-8", xml_declaration=True, pretty_print=True)
    
def generate_default_flowtime(filename):
    settings = {'Ports':[7,8,9], 'Flowtimes':[57, 27, 20], 'Fluid Names':['80% DMSO', '20% DMSO', 'H2 Buffer']}
    pd.DataFrame(settings).to_csv('flowtimes_default.csv', header=True, index=False)

