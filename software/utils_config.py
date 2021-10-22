from lxml import etree as ET
top = ET.Element('settings')

def generate_default_configuration(filename):

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Stripping Buffer Wash')
    sequence.set('Repeat','2')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Rendering Buffer Wash')
    sequence.set('Repeat','3')
    sequence.set('Incubation_Time_in_minute','5')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Rendering Buffer Wash 2')
    sequence.set('Repeat','2')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Imaging Buffer Wash')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Hybridize')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','180')
    sequence.set('Flow_Time_in_second','15')

    setting = ET.SubElement(top,'aspiration_setting')
    setting.set('Pump_Power','0.4')
    setting.set('Duration_Seconds','8')

    tree = ET.ElementTree(top)
    tree.write(filename,encoding="utf-8", xml_declaration=True, pretty_print=True)