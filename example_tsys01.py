""" Example
Showcases functions from the tsys01 module.
"""
import tsys01


def main():    
    #Set up temperature object.
    t = tsys01.TSYS01()

    #Initialize the sensor.
    t.initialize_sensor()       
    
    #Get the temperature in Celsius.
    #Units options: Celsius, degC, C
    temp_c = t.temperature('degC') 
    print(temp_c)
    
    #Get the temperature in Fahrenheit.
    #Units options: Fahrenheit, degF, F    
    temp_f = t.temperature('F')
    print(temp_f)
    
    #Get the temperature in Kelvin.
    #Units options: Kelvin, degK, K    
    temp_k = t.temperature('Kelvin')
    print(temp_k)

    #Take X number of samples in rapid succession,
    #   drop the first and last, then average remaining.
    #Options: number_samples <= 10
    #Unit options: Same as temperature() function.
    temp_burst = t.burst_avg_temperature(number_samples = 10,units = 'degC')
    print(temp_burst)

    #Get the sensor serial number.
    sn = t.sn()
    print(sn)

    #Reset the sensor. Not necessary in most scripts, but helps if there is a PROM error.
    t.reset_sensor()

if __name__ == "__main__":
    main()