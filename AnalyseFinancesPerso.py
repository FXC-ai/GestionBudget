#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 14:57:07 2021

@author: oem
"""

import pandas as pd
import csv
import re

list_DataSet = list()


with open('Releve_031121.csv', newline='', encoding='latin-1') as csvfile :
    reader = csv.reader(csvfile)
    for row in reader:           
        list_temp = []
        for str_elt in row :           
            list_temp.append(str_elt.split(';'))
            
            list_temp_1 = []
            for list_elt in list_temp :
                list_temp_1 = list_temp_1 + list_elt
            
        list_DataSet.append(list_temp_1)

del(list_DataSet[0:12])

for list_transaction in list_DataSet:
    
    int_lenTransaction = len(list_transaction)
    
    if int_lenTransaction == 4 :
        del(list_transaction[3:])
        list_transaction[-1] = float(list_transaction[-1])
    elif int_lenTransaction == 5 :
        del(list_transaction[2])
        del(list_transaction[-1])
        list_transaction[-1] = float(list_transaction[-1])
    elif int_lenTransaction == 7 :
        del(list_transaction[2:5])
        del(list_transaction[-1])
        list_transaction[-1] = float(list_transaction[-1])


df_DataSet = pd.DataFrame(list_DataSet, columns=('Date','Reference','Montant'))


def SimplificationRefMaestro(str_reference):
    match = re.match(r"(^Achat\sMaestro)(\s\w{2}\.\w{2}\.\w{4}\s\w{2}\:\w{2}\s)(.+)(\sNuméro de carte:\s\w{8}$)", str_reference)
    if match :
        return match.groups()[2].lower()
    else:
        return str_reference.lower()
    
    
    
SimplificationRefMaestro('Achat Maestro 15.07.2019 19:39 migrolino Martigny Numéro de carte: 72680131')

type(df_DataSet['Reference'][1])
    
df_DataSet['Reference'] = df_DataSet['Reference'].apply(SimplificationRefMaestro)

df_DataSet_sum = df_DataSet.groupby('Reference').sum()

df_DataSet_sum_sorted = df_DataSet_sum.sort_values(by=['Montant'])

df_DataSet_sum_sorted = df_DataSet_sum_sorted.reset_index()

df_DataSet_sum_sorted['categorie'] = None

dict_items = {
    1 : 'Loyers',
    2 : 'Autres : Vêtements, achâts en pharmacie, achât meubles, cadeaux',
    3 : 'Train',
    4 : 'Entretien voiture et Essence',
    5 : 'Retrait argent',
    6 : 'Nouriture',
    7 : 'Restaurant, take away et Bars',
    8 : 'Virements étrangers',
    9 : 'Assurance et frais de santé',
    10 : 'Sport et loisirs',
    11 : 'Epargne'
    }

serie_categorie = []
def QuelleCategorie (Reference):   
    print(Reference)
    categorie = int(input('Quelle catégorie ?'))
    serie_categorie.append(categorie)


#df_DataSet_sum_sorted['Reference'].apply(QuelleCategorie)

df_stats_references = df_DataSet['Reference'].value_counts()

df_stats_references_1 = df_stats_references.sort_values()




#df_DataSet.set_index('Date', inplace = True)
'''
^Achat\sMaestro\s\w{2}\.\w{2}\.\w{4}\s\w{2}\:\w{2}\s(.+)\sNuméro de carte:\s\w{8}$
^(Achat\sMaestro)(\s\w{2}\.\w{2}\.\w{4}\s\w{2}\:\w{2}\s)(.+)\s(Numéro de carte:\s\w{8})$
(^Achat\sMaestro)(\s\w{2}\.\w{2}\.\w{4}\s\w{2}\:\w{2}\s)(.+)\s(Numéro de carte:\s\w{8}$)

df_DataSet.plot.scatter(x='Date',y='Montant')
df_DataSet.plot(kind='bar')
'''                        
'''
l = list()
for elt in list_DataSet:
    l.append(len(elt))
l.count(4)
l.count(5)
l.count(7)



zip([2,4])
'''