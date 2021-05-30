from lxml import etree as ET
top = ET.Element('settings')

def generate_default_configuration(filename):

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Stripping Buffer Wash')
    sequence.set('Repeat','2')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Stripping Buffer Rinse')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','0.5')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','PBST Wash')
    sequence.set('Repeat','3')
    sequence.set('Incubation_Time_in_minute','5')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Wash (Post Ligation, 1)')
    sequence.set('Repeat','2')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Wash (Post Ligation, 2)')
    sequence.set('Repeat','2')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Stain with DAPI')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','10')
    sequence.set('Flow_Time_in_second','15')

    sequence = ET.SubElement(top,'sequence')
    sequence.set('Name','Ligate')
    sequence.set('Repeat','1')
    sequence.set('Incubation_Time_in_minute','180')
    sequence.set('Flow_Time_in_second','15')

    tree = ET.ElementTree(top)
    tree.write(filename,encoding="utf-8", xml_declaration=True, pretty_print=True)