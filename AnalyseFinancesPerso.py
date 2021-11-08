#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 14:57:07 2021

@author: oem
"""

import pandas as pd
import csv
import re
import pickle as pk

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
        return 'maestro ' + match.groups()[2].lower()
    else:
        return str_reference.lower()
    
    
    
df_DataSet['Reference'] = df_DataSet['Reference'].apply(SimplificationRefMaestro)

df_DataSet_Credit = pd.DataFrame(columns=('Date','Reference','Montant'))

df_DataSet_Debit = pd.DataFrame(columns=('Date','Reference','Montant'))

for row in df_DataSet.iterrows() :   
    if row[1]['Montant'] > 0:
        df_DataSet_Credit = df_DataSet_Credit.append(row[1])
    elif row[1]['Montant'] < 0:
        df_DataSet_Debit = df_DataSet_Debit.append(row[1])


# Tri à partir de tout les débits       
df_DataSet_Debit_OrdreEbanking = pd.DataFrame(columns=('Date','Reference','Montant'))

df_DataSet_Debit_DebitsLSV = pd.DataFrame(columns=('Date','Reference','Montant'))

df_DataSet_Debit_Bancomat = pd.DataFrame(columns=('Date','Reference','Montant'))

df_DataSet_Debit_FraisBank = pd.DataFrame(columns=('Date','Reference','Montant'))

df_DataSet_Debit_AchatMaestro = pd.DataFrame(columns=('Date','Reference','Montant'))


for row in df_DataSet_Debit.iterrows():
    if re.match(r"^ordre e-banking", row[1]['Reference']):
        df_DataSet_Debit_OrdreEbanking = df_DataSet_Debit_OrdreEbanking.append(row[1])
    elif re.match(r"^(débit lsv)\s(.+)", row[1]['Reference']):
        df_DataSet_Debit_DebitsLSV = df_DataSet_Debit_DebitsLSV.append(row[1])
    elif re.match(r"^(bancomat)\s(.+)", row[1]['Reference']) or re.match(r"^(prélèvement)\s(.+)", row[1]['Reference']):
        df_DataSet_Debit_Bancomat = df_DataSet_Debit_Bancomat.append(row[1])
    elif re.match(r"^(frais)\s(.+)", row[1]['Reference']):
        df_DataSet_Debit_FraisBank = df_DataSet_Debit_FraisBank.append(row[1])
    else :
        df_DataSet_Debit_AchatMaestro = df_DataSet_Debit_AchatMaestro.append(row[1])


# Création d'un DataSet avec chaque reference unique
df_DataSet_RefUniq = df_DataSet_Debit_AchatMaestro.groupby('Reference').sum()

df_DataSet_RefUniq['Categorie'] = 0


#Module de chargement du DataSet Complété
with open('df_DataSet_RefUniq.pickle', 'rb') as datas :
    df_DataSet_RefUniq = pk.load(datas)

#Ajout des catégories à chaque débit par carte de df_achatMaestro
df_DataSet_Debit_AchatMaestro['Categorie'] = 0

list_temp_2 = list()
for row in df_DataSet_Debit_AchatMaestro.iterrows():   
    list_temp_2.append(df_DataSet_RefUniq.loc[row[1]['Reference']]['Categorie'])

df_DataSet_Debit_AchatMaestro['Categorie'] = list_temp_2   

#Traitement des Debit LSV
list_temp_3 = list()
for row in df_DataSet_Debit_DebitsLSV.iterrows() :
    print(row[1])
    if re.match(r"^(débit lsv\s)(sunrise)", row[1]['Reference']):
        list_temp_3.append(2)
    elif re.match(r"^(débit lsv\s)(visana)", row[1]['Reference']):
        list_temp_3.append(5)
        
df_DataSet_Debit_DebitsLSV['Categorie'] = list_temp_3

#Traitement des frais bancaires

df_DataSet_Debit_FraisBank['Categorie'] = 6

#Categorisation des retraits d'espece
df_DataSet_Debit_Bancomat['Categorie'] = 1


df_test = df_DataSet_RefUniq.groupby('Categorie').sum()
df_test2 = df_DataSet_Debit_DebitsLSV.groupby('Categorie').sum()
df_test3 = pd.concat([df_test, df_test2])
df_test3 = df_test3.groupby('Categorie').sum()
df_test3.plot(kind='bar')
#df_DataSet_Debit_AchatMaestro['Categorie'].apply(lambda : return df_D)
'''
df_test = df_DataSet_RefUniq.sort_values(by=['Categorie'])
df_test = df_DataSet_RefUniq.groupby('Categorie').sum()

total = len(df_DataSet_Debit_OrdreEbanking) + len(df_DataSet_Debit_DebitsLSV) + len(df_DataSet_Debit_Bancomat) + len(df_DataSet_Debit_FraisBank) + len(df_DataSet_Debit_AchatMaestro)

    
df_DataSet_Debit_Bancomat['Montant'].sum()
df_DataSet_Debit_AchatMaestro['Montant'].sum()
df_DataSet_Debit_AchatMaestro['Montant'].mean()
df_DataSet_Debit_OrdreEbanking['Montant'].sum()
df_DataSet_Debit_FraisBank['Montant'].sum()


df_DataSet_Credit['Montant'].sum() + df_DataSet_Debit['Montant'].sum()
'''
'''
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