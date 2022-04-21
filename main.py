import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pumping_cycle_utils import get_pump_cycles, get_tresholds, populate_statistics

def main(filename_path) -> None:
    """Main function for retrieving cycle pump analysis results"""
    #Load data
    df = pd.read_csv(filename_path)
    #Get last row index as parameter for get_pump_cycles function
    df_last_row = df.shape[0]
    #Convert to datetime dtype
    df["Date"] = pd.to_datetime(df["Date"])

    #Get list of pump cycles
    pump_cycles_list = get_pump_cycles(dataframe=df,last_row_index=df_last_row,start_time_offset=10,end_time_offset=-5)
    
    #Get and new dataframe storing treshold data
    df_treshold = get_tresholds(dataframe=df,pump_cycles=pump_cycles_list)
    #Print mean value for all tresholds
    print("{0}Pumping Cycle Treshold Results{0}".format("="*10))
    print("Mean = {} Pa\n".format(df_treshold["treshold_value"].mean()))
    #Visualise tresholds
    df_treshold.plot(x="treshold_time",y="treshold_value")
    plt.show()

    print("{0}Pumping Cycle Health Analysis Results{0}".format("="*10))
    #Show Kendalls Tau and p-value for all pump cycles
    populate_statistics(dataframe=df,pump_cycles=pump_cycles_list,show_charts=False)

if __name__ == "__main__":
    #Preparing path explicitely in case of moving input file to another folder
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    filename_path = os.path.join(curr_dir,"Pressure.csv")
    #Run program
    print("{0}Pumping Events Detection Assignment{0}\n".format("="*20))
    main(filename_path)

    





