# -*- coding: utf-8 -*-
"""
Created on Thu Nov 17 15:53:19 2016

@author: GJ5356
"""
import pandas as pd
import numpy as np
import os
import time
import math
from pandas.tseries import offsets

GLOBAL_date_column_name ="#Meter Name"# "Date (Period Beginning)" #
GLOBAL_AI_column_suffix = "-AI" #"-AI"
GLOBAL_RI_column_suffix = "-RI"
GLOBAL_RE_column_suffix = "-RE"
GLOBAL_output_statistics= ["Meter code", "Max kWh","Date Max kWh", "Load factor", "Contracted MIC",\
                             "Max kVA","Date Max kVA","kVA 95% quantile", "Average PF",\
                             "Standard deviation PF", "Min PF", "Max PF", "Demand chargeable kVArh", \
                             "Demand exceeded capacity", "Excess availability charge","Reactive power charge", "Required KVAR to reach 0.95 PF" ]
GLOBAL_parameters = "C:\\Users\\GJ5356\\Documents\\Work\\06 - Reporting\\02 - Data Farming\\01 - Power factor\\Power factor parameters.csv"
GLOBAL_PF_multiplier = "C:\\Users\\GJ5356\\Documents\\Work\\06 - Reporting\\02 - Data Farming\\01 - Power factor\\Multiplier Capacitor Power Factor Correction.csv"

##TRIADS: For information, half-hour ending
#["16/01/2013 17:30", "25/11/2013 17:30", "06/12/2013 17:30" ,"30/01/2014 17:30" , "04/12/2014 17:30","19/01/2015 17:30", "02/02/2015 18:00" , "25/11/2015 17:30","19/01/2016 17:30", "15/02/2016 18:30"]
GLOBAL_listTriads =["16/01/2013 17:30", "25/11/2013 17:30", "06/12/2013 17:30" ,\
"30/01/2014 17:30" , "04/12/2014 17:30","19/01/2015 17:30", "02/02/2015 18:00" , \
"25/11/2015 17:30","19/01/2016 17:30", "15/02/2016 18:30"]
GLOBAL_listTriads= pd.to_datetime(GLOBAL_listTriads, format="%d/%m/%Y %H:%M")

def init():
    global myList
    myList = []