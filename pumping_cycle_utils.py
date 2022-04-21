"""Module is storing usefull functions for running pumping cycle analysis"""
from collections import namedtuple
from datetime import datetime, timedelta
from typing import List
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def get_pump_cycles(dataframe,last_row_index: int, start_time_offset: int, end_time_offset: int) -> List[namedtuple]:
    """Function returns a list of pumping cycle attributes represented by named tuple object
    
    PARAMETERS:
    dataframe: Dataframe object
    last_row_index: index of the last row of the data for which main loop should run
    start_time_offset: number of seconds required to start cycle after pump changing state to 1
    start_time_offset: number of seconds required to end cycle before pump changing state to 2 
    
    OUTPUT (named tuple attributes):
    start: represents starting row index position of the pumping cycle
    end: represents ending row index position of the pumping cycle

    Note:
    namedtuple() objects are used in case further attributes would be usefull to retrieve for a pumping cycle
    """
    PumpingCycle = namedtuple("PumpingCycle","start end")
    pump_cycles = []
    started, ended = (0,0) 
    for i in range(last_row_index):
        if dataframe.iloc[i][3] == 1.0 and started == 0: #Check if real start of the pumping cycle
            limit_time_stamp = dataframe.iloc[i][0] + timedelta(seconds=start_time_offset)
            while dataframe.iloc[i][0] < limit_time_stamp:
                i+=1
            start_cycle_index = i #Store dataframe starting index for respective pumping cycle
            started = 1
        if  dataframe.iloc[i][3] == 2.0 and started == 1: #Check if real end of the pumpimpg cyccle
            limit_time_stamp = dataframe.iloc[i][0] + timedelta(seconds=end_time_offset)
            j = i  
            while dataframe.iloc[j][0] > limit_time_stamp:
                j-=1
            end_cycle_index = j #Store dataframe ending index for respective pumping cycle
            started, ended = (0,0)
            pump_cycle = PumpingCycle(start_cycle_index,end_cycle_index)
            pump_cycles.append(pump_cycle)
    return pump_cycles

def get_tresholds(dataframe,pump_cycles: List[namedtuple]) -> pd.DataFrame:
    """Function returns a new dataframe object storing mimimum pressure values for each pump cycle
    
    PARAMETERS:
    dataframe: An original input dataframe, which is required for getting pumping cycle slices
    pump_cycles: A list of pumping cycles attributes
    """
    pump_cycles_minimum_pressure: List[float] = []
    pump_cycles_minimum_time: List[datetime] = []
    for pump in pump_cycles:
        minimum_index = dataframe.iloc[pump.start:pump.end + 1,2].idxmin()
        minimum_time = dataframe.iloc[minimum_index][0]
        minimum_value = dataframe.iloc[minimum_index][2]
        pump_cycles_minimum_pressure.append(minimum_value)
        pump_cycles_minimum_time.append(minimum_time)
    df = pd.DataFrame({"treshold_time": pump_cycles_minimum_time, "treshold_value" : pump_cycles_minimum_pressure})
    return df

def populate_statistics(dataframe,pump_cycles: List[namedtuple],show_charts=False) -> List:
    """Function is populating statistics required cycle trend heath hypothesis rejection/approval
    
    PARAMETERS:
    dataframe: An original input dataframe, which is required for getting pumping cycle slices
    pump_cycles: A list of pumping cycles attributes
    show_charts (OPTIONAL): Allows showing chart for each pumping cycle
    """
    for i, pump in enumerate(pump_cycles):
        pump_cycle_timestamp = dataframe.iloc[pump.start:pump.end + 1,0]
        pump_cycle_pressure =  dataframe.iloc[pump.start:pump.end + 1,2]
        df_corr = pd.DataFrame({"pressure": pump_cycle_pressure,"timestamp": pump_cycle_timestamp})
        #Create an index column, which then will be used for correlaction stats instead of timestamp values
        df_corr["index"] = range(len(pump_cycle_pressure))
        #Get and print correlation results for a pumping cycle
        corr_result = df_corr[["index","pressure"]].corr(method="kendall")
        print(corr_result)
        
        #Convert columns to arrays before entering ttest calculation
        corr_col_array = df_corr["pressure"].values
        index_col_array = df_corr["index"].values
        #Get an print ttest results
        ttest_result = stats.ttest_ind(index_col_array,corr_col_array)
        print("p-value: {0}".format(ttest_result[1]))

        #Show chart for each pumping cycle just in case flag is enabled
        if show_charts:
            df_corr.plot(x="timestamp",y="pressure")
            plt.show()




















    
