# -*- coding: utf-8 -*-
"""
Created on Thu Nov 17 11:01:32 2016

@author: GJ5356
"""

from settings import *

import matplotlib.pyplot as plt  
import seaborn as sns

plt.style.use('ggplot')

GLOBAL_colorRange =  ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']


def _export_chart_to_PNG(data, metercode, xAxis, yAxis):
    print("display")
    fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(8, 13));

    for index, triad in enumerate(data.columns.get_level_values(0).unique()):
        print(triad, index)
        ax= data.loc[:, triad].plot(x=GLOBAL_date_column_name, y="AI", legend=False, x_compat=True, title=triad+ " (MPRN:" +metercode+")", ax=axes[index])
        ax.xaxis.label.set_visible(False)
        ax.set_ylabel("Half-hourly Electricity Consumption [kWh]")
        ax.axvspan(data.loc[data.shape[0]//2-1, (triad, GLOBAL_date_column_name)], data.loc[data.shape[0]//2, (triad, GLOBAL_date_column_name)])

    fig.tight_layout()
    plt.savefig(metercode+".png")    
    plt.show()  
