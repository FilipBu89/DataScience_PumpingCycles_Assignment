"""Module is storing usefull functions for running pumping cycle analysis"""
from collections import namedtuple
from datetime import datetime, timedelta
from typing import List
import pandas as pd
import numpy as np
from scipy import stats
from pandas import DataFrame
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def append_dataframe(dataframe: DataFrame, start_time_offset: int, end_time_offset: int) -> DataFrame:
    """Function creates two new columns for identifying pumping cycles and returns an amended dataframe object
    
    PARAMETERS:
    dataframe: Dataframe object
    start_time_offset: number of seconds required to start cycle after pump changing state to 1
    start_time_offset: number of seconds required to end cycle before pump changing state to 2

    OUTPUT:
    Add 2 new columns to existing Dataframe object:
    [PumpCycle]: determines if item is part of the pumpcing cycle or not; possible values [1/0]
    [PumpStartTime]: shows a real starting time of the respective pump cycle and its also used as grouping attribute
                     pump start time is unique for each pump cycle and therefore can be used as grouping attribute
    """
    def select_offset_time(df: DataFrame,offset_time: int,pump_state: float) -> np.datetime64:
        """Function returns a new start time value if row is identified as pump cycle start
        
        Can be used for adjusting both start and end pump cycle start times
        Used only as func argument for dataframe.apply() method

        PARAMETERS:
        df: DataFrame object
        offset_time: offset time value, which should be added to current datetime value
        pump_state: value, which is in dataset represent as start/end of the pump cycle; e.g. [1.0/2.0]
        """
        if df["PumpState"] == pump_state:
            return pd.to_datetime(df["Date"]) + pd.to_timedelta(offset_time,unit="s")
        else:
            return np.nan

    def identify_pump_cycle(df: DataFrame, pump_state: float) -> int:
        """Function identifies if row in dataset is part of the pump cycle, returns logical value [1/0]

        Filtering is happening on 2 levels:
        - Row is part of the pump start state => represented by [PumpStateFillDown]
        - Row time stamp is within start/end offset time ranges => [PumpEndTime],[PumpStartTime] represent borders
        Used only as func argument for dataframe.apply() method
        
        PARAMETERS:
        df: DataFrame object
        pump_state: value, which storing info about start of the pump cycle within dataset; e.g. [1.0]
        """
        if df["PumpStateFillDown"] == pump_state and \
            pd.to_datetime(df["PumpEndTime"]) > df["Date"] > pd.to_datetime(df["PumpStartTime"]):
            return 1
        else:
            return 0

    #Help column used for identifying pump cycles
    dataframe["PumpStateFillDown"] = dataframe["PumpState"].ffill(axis=0)
    #Get and fill down new pump cycle start time
    dataframe["PumpStartTime"] = dataframe.apply(select_offset_time,args = (start_time_offset,1.0,),axis = 1).ffill(axis=0)
    #Get and fill up new pump cycle end time
    dataframe["PumpEndTime"] = dataframe.apply(select_offset_time,args = (end_time_offset,2.0,),axis = 1).bfill(axis=0)
    #Identify whether row is part of the pump cycle
    dataframe["PumpCycle"] = dataframe.apply(identify_pump_cycle,args = (1.0,),axis = 1)

    #Help columns only, which will not be used in program going forward
    dataframe.drop(columns=["PumpStateFillDown","PumpEndTime"],axis=1,inplace=True)

    return dataframe

def populate_tresholds(dataframe: DataFrame) -> DataFrame:
    """Function for populating pumping cycles treshold resuts

    PARAMETERS:
    dataframe: Dataframe object

    REQUIREMENTS:
    DataFrame objects must have following columns:
    [Date],[Pressure],[PumpCycle],[PumpCycleStartTime]
    
    OUTPUT:
    Prints out Mean value for all pump cycles treshold
    Shows chart with time stamp on X-axis and pressure on Y-axis
    Newly created DF is also returned if needed
    """
    pumps = dataframe[dataframe["PumpCycle"] == 1].sort_values("Pressure").groupby("PumpStartTime", as_index=False).first()
    print("Mean = {} Pa\n".format(pumps["Pressure"].mean()))

    ax = plt.axes()
    ax.plot(pumps.Date,pumps.Pressure)
    ax.xaxis.set_major_locator(plt.MaxNLocator(20))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=90)
    plt.show()

    return pumps

def populate_statistics(dataframe: DataFrame) -> DataFrame:
    """Function populates statistics required for cycle trend heath hypothesis rejection/approval
    
    Returning dataframe object showing only required columns [Correlation], [P-Value] as output

    PARAMETERS:
    dataframe: Dataframe object

    REQUIREMENTS:
    DataFrame objects must have following columns:
    [Pressure],[PumpCycle],[PumpCycleStartTime]
    """
    #Get unique index value for each pump cycle
    dataframe["Index"] = dataframe[dataframe["PumpCycle"] == 1].groupby("PumpStartTime").cumcount()
    #Get and calculate full correlation results
    df_corr_result = dataframe[dataframe["PumpCycle"] == 1].groupby("PumpStartTime")[["Index","Pressure"]].corr(method="kendall").stack().reset_index()
    #Get expected correlation value only per dataset row
    df_corr = df_corr_result.loc[(df_corr_result["level_2"] == "Pressure") & (df_corr_result["level_1"] == "Index")].reset_index()
    #Get and calculate p-value statistics
    df_pvalue = dataframe[dataframe["PumpCycle"] == 1].groupby("PumpStartTime").apply(lambda x: stats.ttest_ind(x["Index"],x["Pressure"]).pvalue).reset_index()
    #Rename calculcated output columns from previous steps
    df_corr.rename(columns={0: "Correlation"},inplace=True)
    df_pvalue.rename(columns={0: "P-Value"},inplace=True)
    #Merge dataframe 
    df_results = pd.concat([df_corr, df_pvalue], axis=1)
    
    return df_results[["Correlation","P-Value"]]

    
