#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 10:46:04 2021

@author: oem
"""

import xml.etree.ElementTree as ET
import re
import pandas as pd

with open('DatasTransactions.xml', 'r') as xmlFile:
    xmlTree = ET.parse(xmlFile)


root = xmlTree.getroot()    

lst_Ntry = root[0][1][8:]

lst_DataSet = []
for et_Ntry in lst_Ntry:

    for c in et_Ntry:
        
        if re.match(r'^({urn:iso:std:iso:20022:tech:xsd:camt.053.001.04})(BookgDt)$', c.tag):
            str_date = c[0].text
            
        elif re.match(r'^({urn:iso:std:iso:20022:tech:xsd:camt.053.001.04})(CdtDbtInd)$', c.tag):
            str_CdtDbtInd = c.text
            
        elif re.match(r'^({urn:iso:std:iso:20022:tech:xsd:camt.053.001.04})(AddtlNtryInf)$', c.tag):
            str_Reference = c.text
            
        elif re.match(r'^({urn:iso:std:iso:20022:tech:xsd:camt.053.001.04})(Amt)$', c.tag):
            str_Montant = c.text


    lst_DataSet.append([str_date, str_CdtDbtInd, str_Reference, str_Montant])
    

for c in lst_Ntry[1025]:
    print('\n',c.text, ' : ')
    for d in c :
        print('-', d.text)
        for e in d :
            print('---',e.text)
            for f in e :
                print('-----', f.text)
                for g in f :
                    print('-------', g)