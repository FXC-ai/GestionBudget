#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 10:46:04 2021

@author: oem
"""

import xml.etree.ElementTree as ET
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np


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

def Choix_Periode (df_DataSet, start, end) :
    
    df_mask = (df_DataSet['Date'] > start) & (df_DataSet['Date'] < end)
    
    return df_DataSet[df_mask] 

def Trie_DebitCredit (df_DataSet):
    
    df_DataSet_DBIT = pd.DataFrame(columns=('Date','Reference','Montant','CdtDbtInd', 'Dbtr', 'Cdtr', 'Mode paiement', 'Categorie'))

    df_DataSet_CRDT = pd.DataFrame(columns=('Date','Reference','Montant','CdtDbtInd', 'Dbtr', 'Cdtr'))
    
    for row in df_DataSet.iterrows() :
        
        CdtDbtInd = row[1]['CdtDbtInd']
        
        if CdtDbtInd == 'DBIT':
            df_DataSet_DBIT= df_DataSet_DBIT.append(row[1])
        elif CdtDbtInd == 'CRDT':
            df_DataSet_CRDT = df_DataSet_CRDT.append(row[1])

    
    return (df_DataSet_DBIT, df_DataSet_CRDT)

def Trie_DBIT_type (df_DataSet_DBIT) :
        
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
            df_DataSet_CRDT['Categorie'][row[0]] = 'Restaurants'
        if row[1]['Dbtr'] == 'Visana Versicherungen AG':
            df_DataSet_CRDT['Categorie'][row[0]] = 'Santé'
            
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Categorie'] != 'Salaire' and (row[1]['Reference'] == 'Crédit' or row[1]['Reference'] == 'Virement postal') and (re.search(r"(MARTINEZ)|(ALLEMAND)|(MANCINI)|(Jagut)",row[1]['Dbtr']) or row[1]['Dbtr'] == 'NOTPROVIDED') and row[1]['Montant'] > 230 and row[1]['Montant'] < 1501:
            df_DataSet_CRDT['Categorie'][row[0]] = 'Loyer'
            
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Dbtr'] == 'Gepimmo SA' :
            df_DataSet_CRDT['Categorie'][row[0]] = 'Loyer'
            
    for row in df_DataSet_CRDT.iterrows():
        if row[1]['Categorie'] == None or row[1]['Reference'] == 'Remboursement Frais Bancaires':
            df_DataSet_CRDT['Categorie'][row[0]] = 'Salaire'    


    return df_DataSet_CRDT

def Categorisation_DBIT_Reference (df_DataSet_DBIT, rgx, str_categorie):
    
    if type(rgx) == list :
        rgx_categorie = '|'.join(rgx)
    else :
        rgx_categorie = rgx
    
    for row in df_DataSet_DBIT.iterrows():
        if re.search(rgx_categorie, row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = str_categorie
    
    return df_DataSet_DBIT
  
def Trieur_RefUniq (df_DataSet):
    
    df_DataSet_RefUniq = df_DataSet.groupby('Categorie').sum()    
    return df_DataSet_RefUniq

def correction_qutenza (df_DataSet_DBIT, str_categorie = 'Virement France'):
    
    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"(pharmacie châteauneu)", row[1]['Reference']) and row[1]['Montant'] > 600:
            df_DataSet_DBIT['Categorie'][row[0]] = str_categorie

    return df_DataSet_DBIT

def Categorisation_EpargneLoyer (df_DataSet_DBIT, df_DataSet_Epargne) :

    for row in df_DataSet_DBIT.iterrows():
        if re.search(r"^(ordre e-banking)$", row[1]['Reference']) and row[1]['Montant'] == 1850 or re.search(r"gepimmo", row[1]['Reference']) :
            df_DataSet_DBIT['Categorie'][row[0]] = 'Loyer'
    
    for dbt in df_DataSet_DBIT.iterrows():
        for epn in df_DataSet_Epargne.iterrows():
            if dbt[1]['Date'] == epn[1]['Date'] and dbt[1]['Montant'] == epn[1]['Montant']:
                df_DataSet_DBIT['Categorie'][dbt[0]] = 'Epargne'
    
    return df_DataSet_DBIT

def Frais_reels (df_DataSet_CRDT_Sum, df_DataSet_DBIT_Sum):
    
    df_Frais_reels = pd.DataFrame(columns=['Categorie', 'Montant'])
    
    for dbt in df_DataSet_DBIT_Sum.iterrows():
        if dbt[0] in df_DataSet_CRDT_Sum.index :            
            df_Frais_reels = df_Frais_reels.append({'Categorie' : dbt[0], 'Montant' : dbt[1]['Montant'] - df_DataSet_CRDT_Sum.loc[dbt[0]]['Montant']}, ignore_index = True)
        else:
            df_Frais_reels = df_Frais_reels.append({'Categorie' : dbt[0], 'Montant' : dbt[1]['Montant']}, ignore_index = True)
                    
    return df_Frais_reels    

def Creation_Pie (periode, df_Frais_reels):
    
    df_Frais_reels_sorted = df_Frais_reels.sort_values(by=['Montant'])
    
    labels = [elt[0] + ':' + str(round(elt[1],1)) + 'CHF' for elt in zip(df_Frais_reels_sorted['Categorie'].tolist(), df_Frais_reels_sorted['Montant'].tolist())]
    
    print(len(labels))
    
    explode = [0.2 for _ in range(len(labels))]
    
    fig1, ax1 = plt.subplots()
    ax1.pie(df_Frais_reels_sorted['Montant'].tolist(), 
            labels = labels,
            explode = explode,
            autopct = lambda pct : "{:.1f}%".format(pct),
            labeldistance = 1.02)
    
    ax1.set_title('Répartition des dépenses du {} au {}'.format(periode[0],periode[1]))
    
    
    plt.show()
    
def Creation_Bar (periode, df_Frais_reels) :

    df_Frais_reels_sorted = df_Frais_reels.sort_values(by=['Montant'])    

    x = [categorie[1].split(':')[0] for categorie in df_Frais_reels_sorted['Categorie'].iteritems()]
    
    fig1, ax1 = plt.subplots()
    ax1.bar(x, 
            df_Frais_reels_sorted['Montant'],
            width = 0.8,
            )
    
    plt.xticks(x, rotation=45, fontsize=8)
    ax1.grid(which='major', axis = 'y')
    
    ax1.set_title('Répartition des dépenses du {} au {}'.format(periode[0],periode[1]))
      
    plt.show()


def Creation_FraisReels (df_DataSet, df_DataSet_Epargne, periode):
    
    df_DataSet_year = Choix_Periode(df_DataSet, periode[0], periode[1])  
    
    df_DataSet_DBIT, df_DataSet_CRDT = Trie_DebitCredit(df_DataSet_year)
    
    df_DataSet_DBIT = Trie_DBIT_type(df_DataSet_DBIT)
    
    simplificateur_ref = Simplificateur_ref(df_DataSet_DBIT).execute()
    
    df_DataSet_DBIT = Simplficateur_refEbanking(df_DataSet_DBIT)
    
    df_DataSet_CRDT = Categorisation_CRDT(df_DataSet_CRDT)
    
    for categorie, references in dict_Categories.items():
        df_DataSet_DBIT = Categorisation_DBIT_Reference(df_DataSet_DBIT, references, categorie)    
    
    df_DataSet_DBIT = correction_qutenza(df_DataSet_DBIT)   
    
    df_DataSet_DBIT = Categorisation_EpargneLoyer(df_DataSet_DBIT, df_DataSet_Epargne)
    
    df_DataSet_DBIT_Sum = df_DataSet_DBIT.groupby('Categorie').sum()
    
    df_DataSet_CRDT_Sum = df_DataSet_CRDT.groupby('Categorie').sum()
    
    df_DataSet_CRDT_sorted = df_DataSet_CRDT.sort_values(by=['Categorie'])
    
    df_Frais_reels = Frais_reels(df_DataSet_CRDT_Sum, df_DataSet_DBIT_Sum)
    
    # df_Frais_reels = df_Frais_reels.sort_values(by=['Montant'])
    
    # df_Frais_reels['Pourcentage'] = round(100*(df_Frais_reels['Montant'] / df_Frais_reels['Montant'].sum()),2)
    
    Creation_Pie(periode, df_Frais_reels)
    
    # Creation_Bar(periode, df_Frais_reels)
    
    return df_Frais_reels


def Creation_BarMultiples (dict_Frais_reels_year, sr_categorie):
    
    df_Frais_reels_Multiple = pd.DataFrame(data = dict_Frais_reels_year)
    
    df_Frais_reels_Multiple['Categorie'] = sr_categorie
    
    df_Frais_reels_Multiple = df_Frais_reels_Multiple.set_index('Categorie')
    
    
    df_Frais_reels_Multiple = df_Frais_reels_Multiple.sort_values(by=[2020])
    
    x = np.arange(len(df_Frais_reels_Multiple))
    int_NbColumns = len(df_Frais_reels_Multiple.columns)
    width = 0.9
    
    fig, ax = plt.subplots()
    
    count = 1
    for int_year in df_Frais_reels_Multiple :
        rects = ax.bar(x - (width / int_NbColumns)*count , df_Frais_reels_Multiple[int_year], width/int_NbColumns, label = int_year)
        
        '''
        count_2 = 0
        for value in x :
            ax.text(value - (width / int_NbColumns)*count, df_Frais_reels_Multiple[int_year][count_2]+125, str(round(df_Frais_reels_Multiple[int_year][count_2],2)), {'rotation' : 90})
            count_2 += 1
        '''
        ax.set_xticklabels((1,2,3,4,5,6,7,8,9,10,11,12,13,14))
        count -= 1
    
    plt.xticks(x, df_Frais_reels_Multiple.index, fontsize = 8)
    ax.grid(which='major', axis = 'y')
    ax.legend()
    ax.set_title('Evolution de la répartition des dépenses par année.')
    plt.show()
    return df_Frais_reels_Multiple

#______________________________________________________________________________

str_balise = '{urn:iso:std:iso:20022:tech:xsd:camt.053.001.04}'

xml_file_Transactions = 'Depenses010122.xml'

xml_file_Epargne = 'Epargne01012022.xml'

dict_Categories = {
    'Restaurant' : ["(le temps d'un)","(la sauvageonne)","(laduree)","(momento)","(take away)",
                       "(paniere)",
                       "(whitefrontier)",
                       "(grenette)",
                       "(scorpion)",
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
                       "(sc.asian food)",
                       "(fournee du gois)",
                       "(tarteline)",
                       "(pret a manger)",
                       "(olympique)",
                       "(pierre herme)",
                       "(burdet salon)",
                       "(la gabaye)"
                       ],
    'Alimentation'  : ["(art des terroirs)","(monop)",
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
                         "(panier sympa)"],
    
    'Sport' : ['(mso sàrl muller roland)|(cie mt blanc)',
              '(refuge)',
              '(cma sa)',
              '(rs equipement)',
              '(televerbier)',
              '(esc[a]*lade)',
              '(bergbahnen)',
              '(ski)',
              '(remont[é|e]es m[e|é]caniq[ues]*)',
              '(vertic)',
              '(sport)',
              '(campeur)',
              '(decat)',
              '(dosenbach)',
              '(grimper)',
              '(télév[i]*erbier)',
              '(cross)',
              '(montagne)'],   
    
    'Santé' : ['(unilabs)',
              '(baziz boissset sonia)',
              '(sandrine chalat)',
              '(hôpital)',
              '(institut central)',
              '(visana)',
              '(visilab)',
              '(sunstore)',
              '(phi mt blanc)'],
    
    'Pharmacie' : ['(pharm[acie]*)','(phie)','(sunstore)','(phi mt blanc)','(pharmacie châteauneu)'],
    
    # 'Voiture' : ['(alliance suisse assurances sa)','(sapn)','(parking)','(park)','(auto)','(marcoz)','(a\.*r\.*e\.*a\.*)','(garage)','(carnot)','(poilu)','(aprr)'],
    
    'Voyage' : ['(tan)','(commune de deauville)','(cmne de chamonix mon)',
               '(clochettes risou)',
               '(s.l.t.c.)',
               '(sbb)',
               '(jugendherberge)',
               '(h[ô|o]tel)',
               '(sncf)',
               '(gare)',
               '(cff)',
               '(bundesbahn)',
               '(tmr)',
               '(bus)',
               '(airport)',
               '(aeroport)',
               '(ratp)'],
    
    'Voiture' : ['(service de la circulation)','(mkt)','(total)','(tamoil)','(eni)','(station)','(bp martigny)', '(alliance suisse assurances sa)','(sapn)','(parking)','(park)','(auto)','(marcoz)','(a\.*r\.*e\.*a\.*)','(garage)','(carnot)','(poilu)','(aprr)'],
    
    'Loisirs' : ['(foire du valais)','(nature&decouvert)',
               '(relay)',
               '(joue[t]*)',
               '(aux feux de la)',
               '(yabio)',
               '(districaj)',
               '(tcd the book of kell)',
               '(sola didact)',
               '(librairie)',
               '(duplirex)',
               '(zerodix)',
               '(gibert)',
               '(zalactor[é|e]e)',
               '(des livres et moi)',
               '(abc)',
               '(mots)',
               '(interdiscount)',
               '(cine)',
               '(raphy darbellay)'
               ],
    
    'Frais bancaires' : ['(frais de clients étrangers)','(frais conto pack)'],
    'Téléphone' : ['(sunrise)','(swisscom)'],
    'Dépenses fonctionnelles' : ['(zalando)',
                              '(etat du valais)',
                              '(snipes)',
                              '(lipo)',
                              '(santa fe)',
                              '(jules)',
                              '(jott)',
                              '(aldm)',
                              '(duplirex)',
                              '(hiob)',
                              '(poste)',
                              '(ikea)',
                              '(shoes)',
                              '(inass)',
                              '(office des pou)',
                              '$(pharmasuisse)^'],    
    
    'Virement France' : '^(ordre e-banking étranger)$',
    'Loyer' : ['(gepimmo)','(martinez)'],
    'Retrait espèce' : '(bancomat)'
    
    }


ET_Ntry = create_ET_Ntry(xml_file_Transactions)

ET_Ntry_Epargne = create_ET_Ntry(xml_file_Epargne)

df_DataSet = create_df_DataSet_Ntry(ET_Ntry, str_balise)

df_DataSet.iloc[1775] = ['2021-04-08','Ordre e-banking', 1850, 'DBIT', 'Francois-Xavier Coindreau', 'Gepimmo']

df_DataSet.loc[len(df_DataSet)] = ['2021-04-08','PharmaSuisse', 282.7, 'DBIT', 'Francois-Xavier Coindreau', 'PharmaSuisse']

df_DataSet.iloc[2159] = ['2021-12-28', 'gepimmo', 1850, 'DBIT', 'François-Xavier Coindreau', 'Gepimmo']

df_DataSet.loc[len(df_DataSet)] = ['2021-12-28', 'service de la circulation', 168, 'DBIT', 'François-Xavier Coindreau', 'Service de la Circulation']

df_DataSet.loc[len(df_DataSet)] = ['2021-12-28', 'alliance suisse assurances sa', 381.7, 'DBIT', 'François-Xavier Coindreau', 'alliance suisse assurances sa']

df_DataSet.iloc[2134] = ['2021-12-09', 'Remboursement Frais Bancaires', 1260,'CRDT' ,'BCVS', 'François-Xavier Coindreau']

df_DataSet_Epargne = create_df_DataSet_Ntry(ET_Ntry_Epargne, str_balise)

df_Frais_reels_2018 = Creation_FraisReels(df_DataSet, df_DataSet_Epargne, ('2018-01-01','2018-12-31'))

df_Frais_reels_2019 = Creation_FraisReels(df_DataSet, df_DataSet_Epargne, ('2019-01-01','2019-12-31'))

df_Frais_reels_2020 = Creation_FraisReels(df_DataSet, df_DataSet_Epargne, ('2020-01-01','2020-12-31'))



periode = ('2021-01-01','2021-12-31')

df_DataSet_2021 = Choix_Periode(df_DataSet, periode[0], periode[1])  
    
df_DataSet_DBIT, df_DataSet_CRDT = Trie_DebitCredit(df_DataSet_2021)

df_DataSet_DBIT = Trie_DBIT_type(df_DataSet_DBIT)
    
simplificateur_ref = Simplificateur_ref(df_DataSet_DBIT).execute()
    
df_DataSet_DBIT = Simplficateur_refEbanking(df_DataSet_DBIT)
    
df_DataSet_CRDT = Categorisation_CRDT(df_DataSet_CRDT)
    
for categorie, references in dict_Categories.items():
    df_DataSet_DBIT = Categorisation_DBIT_Reference(df_DataSet_DBIT, references, categorie)    
    
df_DataSet_DBIT = correction_qutenza(df_DataSet_DBIT)  
    
df_DataSet_DBIT = Categorisation_EpargneLoyer(df_DataSet_DBIT, df_DataSet_Epargne)
    
df_DataSet_DBIT_Sum = df_DataSet_DBIT.groupby('Categorie').sum()
    
df_DataSet_CRDT_Sum = df_DataSet_CRDT.groupby('Categorie').sum()
    
df_DataSet_CRDT_sorted = df_DataSet_CRDT.sort_values(by=['Categorie'])
    
df_Frais_reels_2021 = Frais_reels(df_DataSet_CRDT_Sum, df_DataSet_DBIT_Sum)


Creation_Pie(periode, df_Frais_reels_2021)
dict_Frais_reels_year = { 2018 : df_Frais_reels_2018['Montant'], 2019 : df_Frais_reels_2019['Montant'], 2020 : df_Frais_reels_2020['Montant'], 2021 : df_Frais_reels_2021['Montant']}

test = Creation_BarMultiples(dict_Frais_reels_year, df_Frais_reels_2018['Categorie'])

df_sum_year = pd.DataFrame(dict_Frais_reels_year)
df_sum_years = df_sum_year.sum() - df_sum_year.iloc[2]


