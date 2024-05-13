import pandas as pd
from lxml import etree


def generate_xml_from_dsm(dsm_file,xml_file):
    df = pd.read_csv(dsm_file,index_col=0)
    root = etree.Element('Instance')
    for col_id, col_name in enumerate(df.columns, start=1):
        etree.SubElement(root, 'Instance', id=str(col_id), name=col_name)

    tree_str = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    with open(xml_file,'wb') as f:
        f.write(tree_str)

def update_instances_xml(instances_info,xml_file):
    tree = etree.parse(xml_file)
    root = tree.getroot()

    for instance in root.findall('Instance'):
        instance_id = instance.get('id')
        info = instances_info.get(instance_id)

        if info is not None:
            type_element = etree.SubElement(instance, 'Type')
            type_element.text = info['type']

            content_element = etree.SubElement(instance, 'Content')
            content_element.text = '' if info['type'] == 'Gate' else info['content']

            lane_element = etree.SubElement(instance, 'Lane')
            lane_element.text = info['lane']

    tree.write(xml_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')

def update_condition_xml(dsm_file,xml_file):
    df = pd.read_csv(dsm_file, index_col=0)
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
    except Exception as e:
        root = etree.Element('Processes')
        tree = etree.ElementTree(root)

    for source in df.index:
        for target, value in df.loc[source].items():
            if pd.isna(value):
                continue
            if 'C' in str(value):
                condition_flow = etree.SubElement(root, 'ConditionFlow')
                etree.SubElement(condition_flow, 'Source').text = source
                etree.SubElement(condition_flow, 'Target').text = target
                etree.SubElement(condition_flow, 'Content').text = ""

    tree.write(xml_file, pretty_print=True, xml_declaration=True, encoding='UTF-8')
