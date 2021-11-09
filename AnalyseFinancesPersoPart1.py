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

list_DataSet = creation_DATASET('Releve_031121.csv')
df_Dataset = standardisation_DATASET(list_DataSet)

simplificateur_ref = Simplificateur_ref(df_Dataset)
df_Dataset = simplificateur_ref.execute()

df_DataSet_Credit, df_DataSet_Debit = Trieur_DebitCredit(df_Dataset)

df_DataSet_Debit_OrdreEbanking, df_DataSet_Debit_DebitsLSV, df_DataSet_Debit_Bancomat, df_DataSet_Debit_FraisBank, df_DataSet_Debit_AchatMaestro = Trieur_ModesPaiements(df_DataSet_Debit)