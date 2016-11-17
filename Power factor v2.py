from settings import *

from display import _export_chart_to_PNG


def open_and_clean(path):
    data = pd.read_csv(path, encoding='utf-8', index_col=0, parse_dates=True)#, header=1)
#    print(data.head())
#    data.drop(0, axis=0, inplace=True) # "timestamp"
#    data.set_index(pd.to_datetime(data[GLOBAL_date_column_name], format="%d/%m/%Y %H:%M:%S" ), inplace=True) #"%Y-%m-%d  %H:%M:%S"
    data.fillna(value=0, axis=1, inplace=True)
    data["month"]= data.index.month
#    _export_chart_to_PNG(data,"test", "month", "value")
    contract = Contract(os.path.splitext(path)[0], siteParameters(GLOBAL_parameters))
    contract._add_batch_sites(listMeters(data.columns), data)
    contract._export_statistics_csv()
    contract._export_csv()
     
def is_number(s):
    """
        Boolean function to check if s is a number
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

def listMeters(columns):
    """
        Function that takes a list of meter with AI, RI and RE and return a list of individual MPAN
    """
    list_meters = [x.split("-")[0] for x in columns if is_number(x.split("-")[0])]
    return set(list_meters)


def siteParameters(path):
    param =pd.read_csv(path, header=1)
    param.fillna(0, inplace=True)
    listMPAN = [x for x in param["MPAN's"].str.split("/")]
    param["MPAN's"] = [str(x[1]) for x in listMPAN]
    param.set_index(param["MPAN's"], inplace= True)
        
    for group in listMPAN:
        if len(group)>2:
            for index, newMPAN in enumerate(group):
                if index>1:
                    newRow = param.loc[group[1]]
                    newRow.name = newMPAN
                    param = param.append(newRow)
    return param

class Contract:
    """
        Contract class: a contract is a set of sites gathered under the same name.
        it is possible to add site, remove site from a contract and export all the sites into a CSV file.
    """
    def __init__(self, name, param):
        self.name = name
        self.list_sites = {}
        self.param=param
        self.PFmultiplier = pd.read_csv(GLOBAL_PF_multiplier, index_col=0)
    
    def _add_batch_sites(self, list_meters, data):
        for index, metercode in enumerate(list_meters):  
            
            try:
                mic=float(self.param.loc[metercode,"Sum of Units"])
                price1= float(self.param.loc[metercode,"Sum of Price"])
                price2=float(self.param.loc[metercode,"Sum of Price.2"])
            except:
                mic=0
                price1=0
                price2=0
                
            if metercode+GLOBAL_RI_column_suffix not in data.columns.values and metercode+GLOBAL_RE_column_suffix not in data.columns.values:
                print("no RI/RE "+metercode)
                tmpData = data.loc[:, ["month", metercode+GLOBAL_AI_column_suffix]]
                tmpData["RI"]=0
                tmpData["RE"]=0
            
            elif metercode+GLOBAL_RI_column_suffix not in data.columns.values:
                print("no RI "+metercode)
                tmpData = data.loc[:, ["month", metercode+GLOBAL_AI_column_suffix, metercode+GLOBAL_RE_column_suffix]]
                tmpData["RI"]=0
            elif metercode+GLOBAL_RE_column_suffix not in data.columns.values:
                print("no RE "+metercode)
                tmpData = data.loc[:, ["month", metercode+GLOBAL_AI_column_suffix, metercode+GLOBAL_RI_column_suffix]]
                tmpData["RE"]=0
            else:
                tmpData = data.loc[:, ["month", metercode+GLOBAL_AI_column_suffix, metercode+GLOBAL_RI_column_suffix, metercode+GLOBAL_RE_column_suffix]]
            
            tmpData.columns=["month", "AI", "RI", "RE"]
            self._add_site(metercode,tmpData,mic, price1, price2)

    def _add_site(self, metercode, data, MIC,price1, price2):
        self.list_sites[metercode] = Site(metercode, data, MIC, price1, price2, self.PFmultiplier)     
        
    def _remove_site(self, metercode):
        self.list_sites.pop(metercode, None)      
        
    def _export_csv(self):
        keys= []
        frames = []
        for key, item in self.list_sites.items():
            keys.append(key)
            frames.append(item.data.loc[:, ["AI", "RI", "RE", "Apparent power", "Power factor", "Demand chargeable kVArh", "Demand exceeded capacity"]])

        result = pd.concat(frames, axis=1, keys=keys)

        result.to_csv(self.name+"_fulldata.csv")
    
            
    def _export_statistics_csv(self):
#        keys= []
        frames = []
        for key, item in self.list_sites.items():
            values = item._get_statistics()
#            keys.append(key)
            frames.append(values)

        result = pd.DataFrame(frames, columns= GLOBAL_output_statistics)
        result.to_csv(self.name+ "_statistics.csv", index=False)
        
class Site:
    """ 
        Create a site using meter code, active power and reactive power
        Calculate: apparent power, power factor, demand chargeable, etc.
    """
    def __init__(self, metercode, data, MIC, excess_availability_charge, reactive_power_charge, PFmultiplier):
        self.metercode=metercode
        self.excess_availability_charge= excess_availability_charge
        self.reactive_power_charge = reactive_power_charge
        self.data = data
        self.MIC = MIC
        self.PFmultiplier = PFmultiplier
        #self._rename_columns()
        self._apparent_power()
        self._power_factor()
        self._demand_chargeable()  
        self._demand_exceeded_capacity()
        self._get_triadsdata()
   
    def _get_statistics(self):
        statistics_dict = {}
        statistics_dict["Meter code"]= str(self.metercode)
        statistics_dict["Max kWh"]= self.data["AI"].max()*2
        if math.isnan(self.data["AI"].max()):
            statistics_dict["Load factor"]= 0
            statistics_dict["Date Max kWh"] ="NA"
        else:
            statistics_dict["Load factor"]= self.data["AI"].mean()*2/statistics_dict["Max kWh"]
            statistics_dict["Date Max kWh"]=str(self.data.loc[self.data["AI"]==self.data["AI"].max(), :].index[0])
            
        statistics_dict["Contracted MIC"]= self.MIC
        statistics_dict["Max kVA"]= self.data["Apparent power"].max()*2
        if math.isnan(self.data["Apparent power"].max()):
            statistics_dict["Date Max kVA"]= "NA"
        else:
            statistics_dict["Date Max kVA"]=self.data.loc[self.data["Apparent power"]==self.data["Apparent power"].max(), :].index[0]
        statistics_dict["kVA 95% quantile"]= self.data["Apparent power"].quantile(.95)*2
        statistics_dict["Average PF"]= self.data["Power factor"].mean()
        statistics_dict["Standard deviation PF"]= self.data["Power factor"].std()
        statistics_dict["Min PF"]= float("{0:.2f}".format(self.data["Power factor"].min(axis=0)))
        statistics_dict["Max PF"]= float("{0:.2f}".format(self.data["Power factor"].max(axis=0)))
        statistics_dict["Demand chargeable kVArh"]= self.data["Demand chargeable kVArh"].sum()
        
        if statistics_dict["Min PF"]<0.5: #there is no value to correct power factor if below 0.5
            power_factor=0.5
        else: power_factor=statistics_dict["Min PF"]
        #print(power_factor)
        if math.isnan(power_factor):
            statistics_dict["Required KVAR to reach 0.95 PF"] = 0
        else: 
            statistics_dict["Required KVAR to reach 0.95 PF"] = self.PFmultiplier.loc[power_factor, "0.95"]*statistics_dict["Max kWh"]
            #print("corrector :" + str(self.PFmultiplier.loc[power_factor, "0.95"]))   
            
        unitCharge=0
#        print(self.data["month"].unique())
        for month in self.data["month"].unique():
            maxDemand = self.data.loc[self.data["month"]==month, "Demand exceeded capacity"].max() #max kVA demand for the given month
            unitCharge += len(self.data.loc[self.data["month"]==month, :])/48*maxDemand #the charge is in p/kVA/day thus maxDemand x number of day of the month
        
        statistics_dict["Demand exceeded capacity"] = unitCharge
        statistics_dict["Excess availability charge"]= self.excess_availability_charge
        statistics_dict["Reactive power charge"]= self.reactive_power_charge
        
        return statistics_dict
   
        
    def _get_triadsdata(self):
        keys = []
        frames= []
        for triad in GLOBAL_listTriads:
            if triad in self.data.index:
                print("TRIAD :::::::"+ str(triad))
                keys.append("Triad: " +str(triad))
                frames.append(self.data.loc[triad-offsets.Hour(12):triad+offsets.Hour(12),"AI"].reset_index())
        
#        pd.concat(frames, keys=keys, axis=1).to_csv("result_test.csv")
        _export_chart_to_PNG(pd.concat(frames, keys=keys, axis=1), self.metercode, "month", "value")
    
    def _rename_columns(self):
               
        self.data.fillna(0, inplace=True)
        if self.data.shape[1]==3: #There is no RE in the dataset. An empty column for future calculation
            self.data["RE"]=0
            
        self.data.columns = ["month", "AI", "RI", "RE"]
        
    def _apparent_power(self):
        self.data["Apparent power"] = np.sqrt((self.data[["RI","RE"]].max(axis=1)**2 + self.data["AI"]**2))
    
    def _power_factor(self):
        """
        Real power (kwh) / Apparent power (kVA)
        """
        self.data["Power factor"] = self.data["AI"]/ self.data["Apparent power"]
        self.data["Power factor"].fillna(1, inplace=True)
        self.data.loc[np.isinf(self.data["Power factor"]), :]=1 
        
    
    def _demand_chargeable(self):
        self.data["Demand chargeable kVArh"]=0
        self.data["Demand chargeable kVArh"] = np.maximum(self.data[["RI","RE"]].max(axis=1)-(np.sqrt(1/0.95**2-1)*self.data["AI"]), self.data["Demand chargeable kVArh"])
        self.data["Demand chargeable kVArh"].fillna(0, inplace=True)
    
    def _demand_exceeded_capacity(self):
        self.data["Demand exceeded capacity"] = 0
        self.data["Demand exceeded capacity"] = np.maximum(2*self.data["Apparent power"] -self.MIC,  self.data["Demand exceeded capacity"])
        self.data["Demand exceeded capacity"].fillna(0, inplace=True)
        

start_time = time.time()        
path="test_set.csv" #"C:\\Users\\GJ5356\\Documents\\Work\\02 - c3ntinel\\01 - Clients\\06 - Sanofi\\data2015.csv"

open_and_clean(path)

#multiplier = pd.read_csv(GLOBAL_PF_multiplier, index_col=0)
#
#print(multiplier.columns)
#print(multiplier.index)
#print(multiplier.loc[0.90, "0.95" ])

print("--- %s seconds ---" % (time.time() - start_time))
