""" Example
Showcases functions from the ms5837 module.
Utilizes the default resolution of 8192. 
The temperature, pressure, depth, and altitude functions have a 
"resolution" flag, which can be set to 256,512,1024,2048,4096, or 8192.

The higher the value, the greater the data resolution. However, the cost is 
an increase in conversion time. The difference between requesting 256 and 8192
resolution data is about 20 ms.
"""
import ms5837


def main():    
    
    standard_atmosphere = 1013.25 
    
    #Set up pressure object.
    p = ms5837.MS5837()

    #Initialize the pressure sensor.
    p.initialize_sensor()

    #Request temperature from the sensor.
    #Units options: Celsius,degC,C
    #         Fahrenheight,degF,F
    #         Kelvin,degK,K
    temperature = p.temperature(units = 'degC')       
    print(temperature)
    
    #Request pressure from the sensor. Use atmospheric pressure to get 
    #   pressure exerted by water column.
    #Units options: millibar,mbar
    #         hectopascals,hPa
    #         decibar,dbar
    #         bar
    #         pascal,Pa
    #         kilopascals,kPa
    #         atmospheres,atm
    #         psi
    #         Torr, mmHg
    pressure = p.pressure('millibar',standard_atmosphere)
    print(pressure)
    
    
    #Request depth.
    #This is a standalone function and does not require the pressure function
    #   to be run separately. Pressure is required, so it is computed automatically.
    #Units options: meters,m
    #         feet,ft
    #         fathoms,ftm
    #Latitude is used in this calculation. By default it is 45.00000 deg N.
    depth = p.depth(units = 'm' , lat = 45.00000)
    print(depth)
    
    
    #Request altitude.
    #Units options: meters, m
    #               feet, ft
    altitude = p.altitude(units = 'm',sea_level_pressure = standard_atmosphere)
    print(altitude)
    
    #Reset the sensor. Not necessary, but helps if there is a PROM error.
    p.reset_sensor()
    
    
if __name__ == "__main__":
    main()