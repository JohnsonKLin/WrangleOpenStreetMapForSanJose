#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import xml.etree.cElementTree as ET
import pprint
import json
CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
expected_street = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons",'Loop','East','West','Way','Circle','Highway','Expressway']
street_mapping = { "St": "Street",
            "St.": "Street",
            "Ave":"Avenue",
            "Rd.":"Road",
            "Loop":"",
            "Winchester" : "Winchester Street",
            'Ln':'Lane',
            'Rd':"Road",
            'ave':'Avenue',
            'Hwy':'Highway',
            'Dr':"Drive",
            'Cir':'Circle',
            'street':'Street'
            }
city_mapping = {
u'San José':'San Jose',
'San jose':'San Jose',
'san Jose':'San Jose',
'san jose':'San Jose',
'SUnnyvale':'Sunnyvale',
'Sunnyvale, CA':'Sunnyvale',
'cupertino':'Cupertino',
'Saj Jose':'San Jose',
'santa clara':'Santa Clara',
'Los Gato':'Los Gatos',
'Los Gatos, CA': 'Los Gatos'
}
state_mapping = {
'Ca':'CA',
'California':'CA',
'ca':'CA'
}
SANJOSE_JSON = "sjs.json"
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
phone_type_re = re.compile(r'\d+', re.IGNORECASE)
def iter_tag(filename):
    with open(SANJOSE_JSON, 'wb') as output:
        for event,elem in ET.iterparse(filename):
            node = shape_element(elem)
            if node is not None:
                output.write(json.dumps(node).encode('utf8')+str('\n'))
def phone_cleaning(raw_phone):
    phone_string = ''
    phone_type_re.findall(raw_phone)
    for num in phone_type_re.findall(raw_phone):
        phone_string = phone_string + str(num)
        if len(phone_string) == 10:
            phone_string = str('+1')+phone_string
        elif len(phone_string) == 11:
            phone_string = str('+') + phone_string
    return phone_string

def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" or element.tag == 'relation':
        node['id'] = element.attrib['id']
        if element.tag == 'node':
            node['node_type'] = 'node'
        elif element.tag == 'way':
            node['node_type'] = 'way'
            node_refs = []
            for nd in element.iter("nd"):
                node_refs.append(nd.attrib['ref'])
                node['node_refs'] = node_refs
        elif element.tag == 'relation':
            node['node_type'] = 'relation'
            for tg in element.iter('member'):
                members = []
                member = {}
                members_args = ['ref','role','type']
                for m_args in members_args:
                    if m_args in tg.attrib:
                        member[m_args] = tg.attrib[m_args]
                    members.append(member)
                node['members'] = members
        created = {}
        for cr in CREATED:
            created[cr] = element.attrib[cr]
        node['created'] = created
        if 'lat' in element.attrib:
            node['pos'] = [element.attrib['lat'],element.attrib['lon']]
        address = {}
        for tg in element.iter('tag'):
            if ':' not in tg.attrib['k']:
                if tg.attrib['k'] == 'phone':
                    #clean phone format
                    node[tg.attrib['k']] = phone_cleaning(tg.attrib['v'])
                else:
                    node[tg.attrib['k']] = tg.attrib['v']
            else:
                if tg.attrib['k'].startswith('addr:'):
                    #clean street name 
                    if tg.attrib['k'] == 'addr:street':
                        m =street_type_re.search(tg.attrib['v'])
                        if m:
                            st = m.group()
                            if st not in street_mapping:
                                address['street'] = tg.attrib['v']
                            else:
                                node[tg.attrib['k']] = tg.attrib['v'].replace(st,street_mapping[st])
                        node['address'] = address
                    elif tg.attrib['k'] == 'addr:housenumber':
                        address['housenumber'] = tg.attrib['v']
                        node['address'] = address
                    elif tg.attrib['k'] == 'addr:city':
                        if tg.attrib['v'] not in city_mapping:
                            address['city'] = tg.attrib['v']
                        else:
                            #clean city name 
                            address['city'] = city_mapping[tg.attrib['v']]
                        node['address'] = address
                    elif tg.attrib['k'] == 'addr:postcode':
                        address['postcode'] = tg.attrib['v']
                        node['address'] = address
                    elif tg.attrib['k'] == 'addr:state':#clean state name
                        if tg.attrib['v'] not in state_mapping:
                            address['state'] = tg.attrib['v']
                        else:
                            address['state'] = state_mapping[tg.attrib['v']]
                        node['address'] = address
                else:# shape k "AAA:BBB:CCC" as json format "AAA":{"BBB":"CCC"}
                    leng = len(tg.attrib['k'].split(':')) 
                    temp_dic = {}
                    temp_dic2 = {}
                    if leng == 2:
                        temp_dic[tg.attrib['k'].split(':')[1]] =  tg.attrib['v']
                        node[tg.attrib['k'].split(':')[0]] = temp_dic
                    elif leng == 3:
                        temp_dic2[tg.attrib['k'].split(':')[2]] = tg.attrib['v']
                        temp_dic[tg.attrib['k'].split(':')[1]] =  temp_dic2
                        node[tg.attrib['k'].split(':')[0]] = temp_dic

        return node
    else:
        return None

def run():
    tags = iter_tag('san-jose_california_sample.osm')
if __name__ == "__main__":
    run()
