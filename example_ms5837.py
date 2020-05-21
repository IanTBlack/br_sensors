""" Example
Showcases functions from the ms5837 module.
"""
import ms5837


def main():    
    
    resolution = 8192 #Resolution at which to get data in.
    reference_atmosphere = 1013.25 
    
    #Set up pressure object.
    p = ms5837.MS5837()

    #Initialize the pressure sensor.
    p.initialize_sensor()

    #Request temperature from the sensor.
    #Units options: Celsius,degC,C
    #         Fahrenheight,degF,F
    #         Kelvin,degK,K
    temperature = p.temperature(units = 'degC',resolution = resolution)       
    print(temperature)
    
    #Request pressure from the sensor.
    #Units options: millibar,mbar
    #         hectopascals,hPa
    #         decibar,dbar
    #         bar
    #         pascal,Pa
    #         kilopascals,kPa
    #         atmospheres,atm
    #         psi
    #         Torr, mmHg
    pressure = p.pressure('millibar',reference_atmosphere,resolution)
    print(pressure)
    
    
    #Request depth from the sensor.
    #This is a standalone function and does not require the pressure function
    #   to be run separately. Pressure is required, so it is computed automatically.
    #Units options: meters,m
    #         feet,ft
    #         fathoms,ftm
    #Latitude is used in this calculation. By default it is 45.00000 deg N.
    depth = p.depth('m',resolution = resolution, lat = 45.00000)
    print(depth)
    
    
    #Reset the sensor. Not necessary, but helps if there is a PROM error.
    p.reset_sensor()
    
    
if __name__ == "__main__":
    main()