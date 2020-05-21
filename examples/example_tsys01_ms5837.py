""" Example

Requests temperature from the TSYS01, then requests depth from the MS5837,
    and then applies a timestamp to that data. Final product is a dataframe 
    that contains columns for datetime, temperature, and depth.

Note: This example does not consider the time it takes to request data 
    from each sensor, so the time difference between the time reported and the
    time the sample was taken can be ~30-35 milliseconds. 

    For reference, the time to request data for the TSYS01 is coded to be 10ms.
    For reference, the time to request data for the MS5837 is coded
        to be (at most) 20ms.

    For most field applications, this difference can be considered negligible.

"""
import datetime
import pandas as pd
import time

import tsys01
import ms5837


def main():    
    #Set up temperature and pressure objects.
    t = tsys01.TSYS01()
    p = ms5837.MS5837()

    #Initialize each sensor.
    t.initialize_sensor()  
    p.initialize_sensor()
    
    #If taking an initial air sample, the reference pressure must be in mbar.
    atmo_pressure = p.absolute_pressure()
  
    df = pd.DataFrame() #Holder for data.
    for i in range(10):  #Collect data ~ once per second for 10 seconds.
        temperature = t.temperature('degC') #Get the temp from the TSYS01.
        depth = p.depth('meters',atmo_pressure)  #Get the depth from the MS5837.
        now = pd.to_datetime(datetime.datetime.utcnow()) #Get the time in UTC.
        data = {'datetime':[now],'temperature':[temperature],'depth':[depth]}
        d = pd.DataFrame(data = data)  #Throw the data into a dataframe.
        df = pd.concat([df,d])  #Concatenate previous loop.
        time.sleep(1 - 0.02 - 0.02) #Consider conversion times for sensors.
        print('Timer: {} s'.format(i))
    df = df.reset_index(drop = True)
    print(df)

    
    
    
    
    
if __name__ == "__main__":
    main()