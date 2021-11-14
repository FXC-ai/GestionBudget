#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 11:10:22 2021

@author: oem
"""

import pandas as pd
import csv
import re
import pickle as pk




def load_file (str_fileName) :
    with open(str_fileName + '.pickle', 'rb') as datas :
        return pk.load(datas)




#Categorisation à la main des references uniques
df_DataSet_RefUniq = load_file('df_DataSet_RefUniq')

