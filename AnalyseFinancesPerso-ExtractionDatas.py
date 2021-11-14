#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 16:28:27 2021

@author: oem
"""

import pandas as pd
import csv
import re
import pickle as pk


#Extraction des données

def creation_DATASET (csv_file):
    list_DataSet = list()
    
    with open(csv_file, newline='', encoding='latin-1') as csvfile :
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
    
    return list_DataSet
 
def standardisation_DATASET(list_DataSet):
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
            
    return pd.DataFrame(list_DataSet, columns=('Date','Reference','Montant'))

class Simplificateur_ref ():
    
    def __init__(self, df_Dataset):
        self.df_Dataset= df_Dataset

    def SimplificationRefMaestro(self, str_reference):
        match = re.match(r"(^Achat\sMaestro)(\s\w{2}\.\w{2}\.\w{4}\s\w{2}\:\w{2}\s)(.+)(\sNuméro de carte:\s\w{8}$)", str_reference)
        if match :
            return 'maestro ' + match.groups()[2].lower()
        else:
            return str_reference.lower()
           
    def execute(self):
        self.df_Dataset['Reference'] = self.df_Dataset['Reference'].apply(self.SimplificationRefMaestro)
        return self.df_Dataset

def Trieur_DebitCredit (df_Dataset):
    
    df_DataSet_Credit = pd.DataFrame(columns=('Date','Reference','Montant'))
    df_DataSet_Debit = pd.DataFrame(columns=('Date','Reference','Montant'))
    
    for row in df_Dataset.iterrows() :   
        if row[1]['Montant'] > 0:
            df_DataSet_Credit = df_DataSet_Credit.append(row[1])
        elif row[1]['Montant'] < 0:
            df_DataSet_Debit = df_DataSet_Debit.append(row[1])
            
    return (df_DataSet_Credit, df_DataSet_Debit)

def Trieur_ModesPaiements(df_DataSet_Debit):
    
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

    return (df_DataSet_Debit_OrdreEbanking, df_DataSet_Debit_DebitsLSV, df_DataSet_Debit_Bancomat, df_DataSet_Debit_FraisBank, df_DataSet_Debit_AchatMaestro)

#Categorisation des transactions

def Trieur_RefUniq (df_DataSet):
    df_DataSet_RefUniq = df_DataSet.groupby('Reference').sum()    
    return df_DataSet_RefUniq

def load_file (str_fileName) :
    with open(str_fileName + '.pickle', 'rb') as datas :
        return pk.load(datas)

def save_file (str_fileName, df_DataSet) :
    with open(str_fileName + '.pickle', 'wb') as datas :
        pk.dump(df_DataSet, datas, pk.HIGHEST_PROTOCOL)

def Categorisation_AchatMaestro (df_DataSet_RefUniq, df_DataSet_Debit_AchatMaestro):
    list_temp_2 = list()
    for row in df_DataSet_Debit_AchatMaestro.iterrows():   
        list_temp_2.append(df_DataSet_RefUniq.loc[row[1]['Reference']]['Categorie'])

    df_DataSet_Debit_AchatMaestro['Categorie'] = list_temp_2  

def Trie_MontUniq (df_DataSet):
    df_DataSet_MontUniq = df_DataSet.sort_values(['Montant'])
    return df_DataSet_MontUniq
    
def Tri_Credit (df_DataSet_Credit):
    list_temp_3 = list()
    for row in df_DataSet_Credit.iterrows():    
        if row[1]['Montant'] > 406 and row[1]['Montant'] <= 610:
            list_temp_3.append(17)
        elif row[1]['Montant'] > 3999:
            list_temp_3.append(16)
        else :
            list_temp_3.append(21)

    df_DataSet_Credit['Categorie'] = list_temp_3
    
    return df_DataSet_Credit

def Tri_Prelevements (df_DataSet_Debit_DebitsLSV) :

    list_temp_4 = list()
    for row in df_DataSet_Debit_DebitsLSV.iterrows() :
        if re.match(r"^(débit lsv\s)(sunrise)", row[1]['Reference']):
            list_temp_4.append(2)
        elif re.match(r"^(débit lsv\s)(visana)", row[1]['Reference']):
            list_temp_4.append(5)
            
    df_DataSet_Debit_DebitsLSV['Categorie'] = list_temp_4
    return df_DataSet_Debit_DebitsLSV

def Tri_OrdreEbanking (df_DataSet_Debit_OrdreEbanking):
    list_temp_5 = list()
    for row in df_DataSet_Debit_OrdreEbanking.iterrows():    
        if row[1]['Montant'] == -1850 :
            list_temp_5.append(4)
        elif row[1]['Reference'] == 'ordre e-banking étranger':
            list_temp_5.append(3)
        else :
            list_temp_5.append(0)

    df_DataSet_Debit_OrdreEbanking['Categorie'] = list_temp_5
    
    return df_DataSet_Debit_OrdreEbanking

list_DataSet = creation_DATASET('Releve_031121.csv')
df_Dataset = standardisation_DATASET(list_DataSet)

simplificateur_ref = Simplificateur_ref(df_Dataset)
df_Dataset = simplificateur_ref.execute()

df_DataSet_Credit, df_DataSet_Debit = Trieur_DebitCredit(df_Dataset)

df_DataSet_Debit_OrdreEbanking, df_DataSet_Debit_DebitsLSV, df_DataSet_Debit_Bancomat, df_DataSet_Debit_FraisBank, df_DataSet_Debit_AchatMaestro = Trieur_ModesPaiements(df_DataSet_Debit)

#Pour les achâts par carte de crédit
df_DataSet_RefUniq = Trieur_RefUniq(df_DataSet_Debit_AchatMaestro)
df_DataSet_RefUniq = load_file('df_DataSet_RefUniq')
Categorisation_AchatMaestro(df_DataSet_RefUniq, df_DataSet_Debit_AchatMaestro)    

#Pour les Credits
df_DataSet_Credit['Categorie'] = 0
df_DataSet_Credit = Tri_Credit(df_DataSet_Credit)

#Pour les prélèvements
df_DataSet_Debit_DebitsLSV = Tri_Prelevements(df_DataSet_Debit_DebitsLSV)

#Traitement des frais bancaires
df_DataSet_Debit_FraisBank['Categorie'] = 6

#Categorisation des retraits d'espece
df_DataSet_Debit_Bancomat['Categorie'] = 1

df_DataSet_Debit_OrdreEbanking = Tri_OrdreEbanking(df_DataSet_Debit_OrdreEbanking)

'''
def Save_DataSet (dict_DataSet):
    for fileName, df in dict_DataSet.items():        
        with open(fileName+'.pickle', 'wb') as current_file :
            pk.dump(df, current_file)        

def Save_dict_DataSet (dict_DataSet):
    with open('dict_DataSet.pickle', 'wb') as current_file :
         pk.dump(current_file, dict_DataSet)   


def save_file(fileName, df):
    
    with open(fileName+'pickle', 'w') as current_file :
        pk.dump(current_file, df)
'''