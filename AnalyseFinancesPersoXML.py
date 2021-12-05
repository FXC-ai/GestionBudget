#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 10:46:04 2021

@author: oem
"""

import xml.etree.ElementTree as ET
import pandas as pd
import re


def create_ET_Ntry (xml_file):
    ET_tree = ET.parse(xml_file)
    ET_root = ET_tree.getroot()   
    ET_Ntry = ET_root[0][1].findall(str_balise + 'Ntry')
    
    return ET_Ntry


def create_df_DataSet_Ntry (ET_Ntry, str_balise):
    list_Ntry = list()
    
    for Ntry in ET_Ntry :   
        Date = Ntry.find(str_balise + 'BookgDt').find(str_balise+'Dt').text
        Montant = float(Ntry.find(str_balise + 'Amt').text)
        Reference = Ntry.find(str_balise + 'AddtlNtryInf').text
        CdtDbtInd = Ntry.find(str_balise + 'CdtDbtInd').text
        NtryDtls = Ntry.find(str_balise + 'NtryDtls')  
        Dbtr = 'NOTPROVIDED'
        Cdtr = 'NOTPROVIDED'
        
        if NtryDtls != None :
            try :
                Dbtr = NtryDtls.find(str_balise + 'TxDtls').find(str_balise + 'RltdPties').find(str_balise + 'Dbtr').find(str_balise + 'Nm').text
            except:
                Dbtr = 'NOTPROVIDED'            
            try :
                Cdtr = NtryDtls.find(str_balise + 'TxDtls').find(str_balise + 'RltdPties').find(str_balise + 'Cdtr').find(str_balise + 'Nm').text
            except :
                Cdtr = 'NOTPROVIDED'                 
            try :
                Note = NtryDtls.find(str_balise + 'TxDtls').find(str_balise + 'RmtInf').find(str_balise + 'Ustrd').text
                #print(Note)
            except :
                pass


            
            
        
        list_Ntry.append([Date, Reference, Montant, CdtDbtInd, Dbtr, Cdtr])

    df_DataSet = pd.DataFrame(list_Ntry, columns=('Date','Reference','Montant','CdtDbtInd', 'Dbtr', 'Cdtr'))
    
    return df_DataSet


def Trie_DebitCredit (df_DataSet):
    
    df_DataSet_DBIT = pd.DataFrame(columns=('Date','Reference','Montant','CdtDbtInd', 'Dbtr', 'Cdtr'))
    df_DataSet_CRDT = pd.DataFrame(columns=('Date','Reference','Montant','CdtDbtInd', 'Dbtr', 'Cdtr'))
    
    for row in df_DataSet.iterrows() :
        
        CdtDbtInd = row[1]['CdtDbtInd']
        
        if CdtDbtInd == 'DBIT':
            df_DataSet_DBIT= df_DataSet_DBIT.append(row[1])
        elif CdtDbtInd == 'CRDT':
            df_DataSet_CRDT = df_DataSet_CRDT.append(row[1])

    
    return (df_DataSet_DBIT, df_DataSet_CRDT)


def Trie_DBIT_type (df_DataSet_DBIT) :
    
    df_DataSet_DBIT['Mode paiement'] = None
    
    dict_regex_ModePaiement = {"Achat Maestro" : 'Achat Maestro' ,
                               "Bancomat" : 'Retrait',
                               "ordre" : 'Ordre E-banking' ,
                               "Ordre" : 'Ordre E-banking' ,
                               "Débit" : 'Prelevement',
                               "Frais" : 'Prelevement'}

    for row in df_DataSet_DBIT.iterrows():
            
        match = re.search(r"([O|o]rdre)|(Achat Maestro)|(Bancomat)|(Débit)|(Frais)", row[1]['Reference']) 
        
        if match :
            df_DataSet_DBIT['Mode paiement'][row[0]] = dict_regex_ModePaiement[match.group()]

    return df_DataSet_DBIT

class Simplificateur_ref ():
    
    def __init__(self, df_Dataset):
        self.df_Dataset= df_Dataset

    def SimplificationRefMaestro(self, str_reference):
        match = re.match(r"(^Achat\sMaestro)(\s\w{2}\.\w{2}\.\w{4}\s\w{2}\:\w{2}\s)(.+)(\sNuméro de carte:\s\w{8}$)", str_reference)
        if match :
            return match.groups()[2].lower()
        else:
            return str_reference.lower()
           
    def execute(self):
        self.df_Dataset['Reference'] = self.df_Dataset['Reference'].apply(self.SimplificationRefMaestro)
        return self.df_Dataset

def Simplficateur_refEbanking (df_DataSet_DBIT):
    
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"^(ordre e-banking)$", row[1]['Reference']) and row[1]['Cdtr'] != 'NOTPROVIDED' :
            df_DataSet_DBIT['Reference'][row[0]] = row[1]['Cdtr'].lower()
    
    return df_DataSet_DBIT
    
def Categorisation_CRDT (df_DataSet_CRDT):
    
    df_DataSet_CRDT['Categorie'] = None
    
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Montant'] > 3999 :
            df_DataSet_CRDT['Categorie'][row[0]] = 'Salaire'
            
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Dbtr'] == 'Pharmacies BENU SA':
            df_DataSet_CRDT['Categorie'][row[0]] = 'Remboursement RestaurantBENU'
        if row[1]['Dbtr'] == 'Visana Versicherungen AG':
            df_DataSet_CRDT['Categorie'][row[0]] = 'Remboursement Assurance'
            
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Categorie'] != 'Salaire' and (row[1]['Reference'] == 'Crédit' or row[1]['Reference'] == 'Virement postal') and (re.search(r"(MARTINEZ)|(ALLEMAND)|(MANCINI)|(Jagut)",row[1]['Dbtr']) or row[1]['Dbtr'] == 'NOTPROVIDED') and row[1]['Montant'] > 230 and row[1]['Montant'] < 1501:
            df_DataSet_CRDT['Categorie'][row[0]] = 'Remboursement Loyer'
            
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Dbtr'] == 'Gepimmo SA' :
            df_DataSet_CRDT['Categorie'][row[0]] = 'Remboursement Chauffage'
            
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Categorie'] == None :
            df_DataSet_CRDT['Categorie'][row[0]] = 'Remboursement Inconnu'    

    return df_DataSet_CRDT

def Categorisation_DBIT (df_DataSet_DBIT):
    
    df_DataSet_DBIT['Categorie'] = None
    
    list_restaurants = ["(le temps d'un)","(la sauvageonne)",
                       "(paniere)",
                       "(whitefrontier)",
                       "(grenette)",
                       "(engrenage)",
                       "(le panetier)",
                       "(martigny boutique ho)",
                       "(holy cow)",
                       "(montreux jazz expres)",
                       "(grotto)",
                       "(la vache qui vole)",
                       "(kitsch inn)",
                       "(cake)",
                       "(newrest)",
                       "(zenhäusern)",
                       "(chirvette)",
                       "(beefore)",
                       "(kebab)",
                       "(burger)",
                       "(pizza)",
                       "(pizzeria)",
                       "(restaurant)",
                       "(moo)",
                       "(donald)",
                       "(biére)",
                       "(brioche)",
                       "(michello)",
                       "(coffee)",
                       "(cafe)",
                       "(boul[angerie]*)",
                       "(bar)",
                       "(pain)",
                       "(wfb sarl)",
                       "(the 7th floor)",
                       "(shed)",
                       "(petits pois carottes)",
                       "(antan)",
                       "(pitz)",
                       "(dely)",
                       "(crêperie)",
                       "(les iles)",
                       "(pret-a-manager)",
                       "(le pigalle)",
                       "(cantine)",
                       "(happy tracks)",
                       "(applegreen)",
                       "(hell cat maggies)",
                       "(oliver st john gogar)",
                       "(the landmark)",
                       "(starbucks)",
                       "(syrtos)",
                       "(little boxes)",
                       "(les delices)",
                       "(chandolin boutique)",
                       "(king long store)",
                       "(ristorante)",
                       "(hydromel)",
                       "(ela)",
                       "(fournil)",
                       "(chalet de cuvery)",
                       "(le tramway)",
                       "(sc asian food)",
                       "(fournee du gois)",
                       "(tarteline)",
                       "(pret a manger)",
                       "(olympique)",
                       "(pierre herme)",
                       "(burdet salon)",
                       "(la gabaye)"
                       ]
    
    list_alimentation = ["(art des terroirs)",
                         "(kiosque de bovernier)",
                         "(siverino)",
                         "(spar)",
                         "(sas passy dis)",
                         "(boucherie)",
                         "(le chapiteau romain)",
                         "(payot)",
                         "(attila)",
                         "(volg)",
                         "(monoprix)",
                         "(intermarche)",
                         "(panier dasie)",
                         "(huit a huit)",
                         "(migro)",
                         "(coop)",
                         "(lidl)",
                         "(denner)",
                         "(super u)",
                         "(franprix)",
                         "(grand frais)",
                         "(leclerc)",
                         "(aldi)",
                         "(carrefour)",
                         "(casabio)",
                         "(auchan)",
                         "(sas ndp alimentation)",
                         "(edelweiss market)",
                         "(espace japon)",
                         "(sas ndp distribution)",
                         "(sc asian food)",
                         "(panier sympa)"]
    
    rgx_restaurants = '|'.join(list_restaurants)
    rgx_alimentation = '|'.join(list_alimentation)

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(mkt)|(total)|(tamoil)|(eni)|(station)|(bp martigny)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Voiture Essence'

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(alliance suisse assurances sa)|(sapn)|(park)|(auto)|(marcoz)|(a\.*r\.*e\.*a\.*)|(garage)|(carnot)|(poilu)|(aprr)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Voiture'
            
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"bancomat", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Retrait Bancomat'

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(mso sàrl muller roland)|(cie mt blanc)|(refuge)|(cma sa)|(rs equipement)|(televerbier)|(esc[a]*lade)|(bergbahnen)|(ski)|(remont[é|e]es m[e|é]caniq[ues]*)|(vertic)|(sport)|(campeur)|(decat)|(dosenbach)|(grimper)|(télév[i]*erbier)|(cross)|(montagne)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Sport'            
            
    for row in df_DataSet_DBIT.iterrows():
        if re.search(rgx_alimentation, row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Alimentation'  
    
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(unilabs)|(baziz boissset sonia)|(sandrine chalat)|(hôpital)|(institut central)|(visana)|(visilab)|(pharm[acie]*)|(phie)|(sunstore)|(phi mt blanc)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Assurance Santé / Frais de santé' 

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(pharm[acie]*)|(phie)|(sunstore)|(phi mt blanc)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Frais de Pharmacie'
        if re.search(r"(pharmacie châteauneu)", row[1]['Reference']) and row[1]['Montant'] > 600:
            df_DataSet_DBIT['Categorie'][row[0]] = 'Inclassable'
        if re.search(r"(pharmasuisse)", row[1]['Reference']):
            df_DataSet_DBIT['Categorie'][row[0]] = 'Inclassable'

    for row in df_DataSet_DBIT.iterrows():
        if re.search(rgx_restaurants, row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Restaurants Bars Patisseries TakeAway'
    
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(tan)|(clochettes risou)|(s.l.t.c.)|(sbb)|(jugendherberge)|(h[ô|o]tel)|(sncf)|(gare)|(cff)|(bundesbahn)|(tmr)|(bus)|(airport)|(aeroport)|(ratp)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Transport / Hotel'

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(foire du valais)|(nature&decouvert)|(relay)|(joue[t]*)|(aux feux de la)|(yabio)|(districaj)|(tcd the book of kell)|(sola didact)|(librairie)|(duplirex)|(zerodix)|(gibert)|(zalactor[é|e]e)|(des livres et moi)|(abc)|(mots)|(interdiscount)|(cine)|(raphy darbellay)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Loisirs : livres, electronique, cinéma, cadeaux, musée'

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(frais de clients étrangers)|(frais conto pack)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Frais bancaires'

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(ordre e-banking étranger)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Virements France'
            
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(ordre e-banking)", row[1]['Reference']) and row[1]['Montant'] == 1850 or re.search(r"gepimmo", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Loyer'
        if re.search(r"(martinez)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Loyer'
    
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(sunrise)|(swisscom)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Téléphone et Internet'
            
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(zalando)|(etat du valais)|(snipes)|(lipo)|(santa fe)|(jules)|(jott)|(aldm)|(duplirex)|(hiob)|(poste)|(ikea)|(shoes)|(inass)|(office des pou)", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Dépenses fonctionelles : vêtements, ameublement, poste, frais administratifs'
            
            
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"^(ordre e-banking)$", row[1]['Reference']) and row[1]['Montant'] != 1850 :
            df_DataSet_DBIT['Categorie'][row[0]] = 'ordre e-banking'         
                
    for row in df_DataSet_DBIT.iterrows():
        if row[1]['Reference'] == 'francois-xavier coindreau' and row[1]['Dbtr'] == 'Francois-Xavier Coindreau' :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Epargne'
            
    for row in df_DataSet_DBIT.iterrows():
        if row[1]['Categorie'] == None :
            df_DataSet_DBIT['Categorie'][row[0]] = 'A classer'
    
    return df_DataSet_DBIT
    
  
def Trieur_RefUniq (df_DataSet):
    df_DataSet_RefUniq = df_DataSet.groupby('Categorie').sum()    
    return df_DataSet_RefUniq


    
str_balise = '{urn:iso:std:iso:20022:tech:xsd:camt.053.001.04}'

xml_file_Transactions = 'DatasTransactions.xml'

xml_file_Epargne = 'DatasEpargne.xml'

ET_Ntry = create_ET_Ntry(xml_file_Transactions)

ET_Ntry_Epargne = create_ET_Ntry(xml_file_Epargne)

df_DataSet = create_df_DataSet_Ntry(ET_Ntry, str_balise)

df_DataSet_Epargne = create_df_DataSet_Ntry(ET_Ntry_Epargne, str_balise)

df_DataSet.iloc[1776] = ['2021-04-08','Ordre e-banking', 1850, 'DBIT', 'Francois-Xavier Coindreau', 'Gepimmo']

df_DataSet.iloc[-1] = (['2021-04-08','PharmaSuisse', 282.7, 'DBIT', 'Francois-Xavier Coindreau', 'PharmaSuisse'])

df_DataSet_DBIT, df_DataSet_CRDT = Trie_DebitCredit(df_DataSet)

df_DataSet_DBIT = Trie_DBIT_type(df_DataSet_DBIT)

simplificateur_ref = Simplificateur_ref(df_DataSet_DBIT).execute()

df_DataSet_DBIT = Simplficateur_refEbanking(df_DataSet_DBIT)

df_DataSet_CRDT = Categorisation_CRDT(df_DataSet_CRDT)

df_DataSet_DBIT = Categorisation_DBIT(df_DataSet_DBIT)

df = df_DataSet_DBIT.sort_values(by=['Categorie'])

df_2 = df_DataSet_DBIT.groupby('Categorie').sum()

df_DataSet_DBIT['Categorie'].value_counts()
