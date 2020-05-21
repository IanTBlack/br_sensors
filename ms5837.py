"""
#Tested on a Raspberry Pi 4.
#Tested in Python 3.7.3 via Spyder 3.3.3.

#Description
    A class for operating the MS5837-02BA and MS5837-30BA over I2C
    on a Raspberry Pi.
    
    Pressure and temperature are calculated per the TE MS5837 manual.
    30BA = https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FMS5837-30BA%7FB1%7Fpdf%7FEnglish%7FENG_DS_MS5837-30BA_B1.pdf%7FCAT-BLPS0017
    02BA = https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=MS5837-02BA01&DocType=DS&DocLang=English
    
    Depth calculation utilizes TEOS-10 gsw_z_from_p.
    
    Altitude utilizes the hypsometric equation.
    
#Pinouts for Blue Robotics MS5837 Series
    MS5837 - RPi
    Red - 3.3v
    Black - GND
    Green - SCL
    White - SDA
    
#Example
    ms5837 = MS5837('30BA')  #Set up class for a MS5837-30BA sensor.
    ms5837.initialize_sensor()  #Initialize the sensor.
    
    #Compute depth in fathoms assuming standard atmosphere and using
        the sensor's highest resolution.
    
    depth = ms5837.depth('fathoms') 
"""

try:  
    import math
    import time  #Used for pausing func to perform ADC temperature conversion.
    import smbus  #Used for I2C comms with TSYS01.
except ImportError: 
    print("The smbus module is required.")
    print("Try 'sudo apt-get install python-smbus' in Terminal.")


class MS5837():
    def __init__(self,model='30BA', bus=1, address=0x76):
        self._reset = 0x1E
        self._read = 0x00 
        self._osr = [256,512,1024,2048,4096,8192] #Resolution options.
        self._conv_d1 = [0x40,0x42,0x44,0x46,0x48,0x4A] #Indexed by OSR.
        self._conv_d2 = [0x50,0x52,0x54,0x56,0x58,0x5A] #Indexed by OSR.
        self._wait_time = [0.001,0.002,0.003,0.005,0.01,0.02] #Indexed by OSR.
        self._prom = [0xA0,0xA2,0xA4,0xA6,0xA8,0xAA,0xAC] #PROM addresses.
        self._model = model.upper()
        self._bus = bus
        self._address = address
        if self._model in ['30BA','02BA']:
            if self._address in [0x76,0x77]:
                try:  
                    self._i2c = smbus.SMBus(self._bus) 
                except: 
                    print("Can't initiate I2C over bus #{}.".format(self._bus))
                    print("1) Do you have python-smbus installed?")
                    print("2) Check device status with 'i2cdetect -y 1'")
                    print("\tor 'i2cdetect -y 0' via Terminal.")
                    print("3) Check SDA/SCL orientation.")
            else:
                print('Address must be 0x77 or 0x76.')
        else:
            print("Model not supported by this module.")


    def initialize_sensor(self): #Reset sensor and get cal coeffs.
        self.reset_sensor()
        self._calibration_data()
        check = (self._cal_data[0] & 0xF000) >> 12
        if check != self._crc4(self._cal_data):
            print("PROM read error, cyclic redundancy check failed.")
            return False
        else:
            return True


    def reset_sensor(self): 
        self._i2c.write_byte(self._address,self._reset)
        time.sleep(0.1)  
        return True

    def _calibration_data(self):
        self._cal_data = []
        for c in self._prom: #Get cal info for each prom address.
            word = self._i2c.read_word_data(self._address,c)
            coeff = ((word & 0xFF) << 8) | (word >> 8) 
            self._cal_data.append(coeff)
            
    
    def _crc4(self,n_prom):
        n_rem = 0
        n_prom[0] = ((n_prom[0]) & 0x0FFF)
        n_prom.append(0)   
        for i in range(16):
            if i%2 == 1:
                n_rem ^= ((n_prom[i>>1]) & 0x00FF)
            else:
                n_rem ^= (n_prom[i>>1] >> 8)
                
            for n_bit in range(8,0,-1):
                if n_rem & 0x8000:
                    n_rem = (n_rem << 1) ^ 0x3000
                else:
                    n_rem = (n_rem << 1)
        n_rem = ((n_rem >> 12) & 0x000F)       
        return n_rem ^ 0x00

            
    def _get_data(self,resolution=8192):
        self._d1 = 0 
        self._d2 = 0
        if resolution not in self._osr:
            print('Not a valid resolution option.')
            print('Valid options are: {}.'.format(self._osr))
            print('Defaulting to 8192.')
            idx = self._osr.index(8192) 
            conv_d1_addr = self._conv_d1[idx]
            conv_d2_addr = self._conv_d2[idx]
            wait = self._wait_time[idx]
        else: #Do the following if the user gives a valid resolution.
            idx = self._osr.index(resolution) 
            conv_d1_addr = self._conv_d1[idx]
            conv_d2_addr = self._conv_d2[idx]
            wait = self._wait_time[idx]

        self._i2c.write_byte(self._address,conv_d1_addr) #Issue conversion.
        time.sleep(wait)
        d1 = self._i2c.read_i2c_block_data(self._address,self._read,3) 
        self._d1 = d1[0] << 16 | d1[1] << 8 | d1[2] 

        self._i2c.write_byte(self._address,conv_d2_addr) 
        time.sleep(wait) 
        d2 = self._i2c.read_i2c_block_data(self._address,self._read,3) 
        self._d2 = d2[0] << 16 | d2[1] << 8 | d2[2] 
        

    def _first_order_calculation(self):
        c1 = self._cal_data[1]
        c2 = self._cal_data[2]
        c3 = self._cal_data[3]
        c4 = self._cal_data[4]
        c5 = self._cal_data[5]
        c6 = self._cal_data[6]     
        self._dt = self._d2 - c5 * 2**8
        if self._model == "30BA":
            self._sens = c1*2**15+(c3*self._dt)/2**8
            self._off = c2*2**16+(c4*self._dt)/2**7
        elif self._model == "02BA":
            self._sens = c1*2**16+(c3*self._dt)/2**7
            self._off = c2*2**17+(c4*self._dt)/2**6        
        self._temp = (2000 + self._dt * c6/(2**23)) #1st order.
           
    
    def _second_order_calculation(self):
        if self._model == "30BA":
            if self._temp/100 < 20:
                ti = 3 * self._dt**2 / 2**33
                offi = 3 * (self._temp - 2000)**2 / 2**1
                sensi = 5 * (self._temp - 2000)**2 / 2**3
                if self._temp/100 < -15:
                    offi = offi + 7 * (self._temp + 1500)**2
                    sensi = 4 * (self._temp + 1500)**2
            elif self._temp/100 >= 20:
                ti =  2* self._dt**2 / 2**37
                offi = 1 * (self._temp-2000)**2 / 2**4
                sensi = 0               
            off2 = self._off - offi
            sens2 = self._sens - sensi
            self.p2 = (((self._d1 * sens2)/2**21-off2)/2**13)/10 #2nd order.
            
        elif self._model == "02BA":
            if self._temp/100 < 20:
                ti = 11 * self._dt**2 / 2**35
                offi = 31 * (self._temp - 2000)**2 / 2**3
                sensi = 63 * (self._temp - 2000)**2  / 2**5       
            off2 = self._off - offi
            sens2 = self._sens - sensi        
            self.p2 = (((self._d1 * sens2)/2**21-off2)/2*15)/100 #2nd order.
        
        self.temp2 = (self._temp - ti)/100 #2nd order.
    
    
    def temperature(self,units='Celsius',resolution=8192):
        
        """Compute second order temperature.
        temp2 is the second order temperature.
        units -- the units the user wants temperature in
        resolution -- the resolution option of the sensor
        """
        
        self._get_data(resolution = resolution)
        self._first_order_calculation()
        self._second_order_calculation()        
        if units in ['Celsius' , 'degC','C']:
            temperature  = self.temp2
        elif units in ['Fahrenheit' , 'degF' , 'F']:
            temperature = 1.8 * self.temp2 + 32
        elif units in ['Kelvin' , 'degK' , 'K']:
            temperature = self.temp2 + 273.15   
        else:
            print('Units not valid. Defaulting to Celsius.')
            temperature = self.temp2
        temperature = round(temperature,2)    
        return temperature

    
    def absolute_pressure(self,units = 'millibar',resolution=8192):
        
        """Compute second order pressure as absolute pressure.
        p2 is the second order temperature compensated pressure in millibars.
        units -- units that the user wants
        resolution -- the resolution option of the sensor.
        """
        
        self._get_data(resolution = resolution)
        self._first_order_calculation()
        self._second_order_calculation()
        self.abs_p = self.p2        
        if units in ['millibar','mbar','hectopascals','hPa']:
            pressure = self.p2 
        elif units in ['decibar','dbar']:
            pressure = self.p2  / 100
        elif units in ['bar']:
            pressure = self.p2  /1000
        elif units in ['pascal','Pa']:
            pressure = self.p2  * 100
        elif units in ['kilopascals','kPa']:
            pressure = self.p2  / 10
        elif units in ['atmospheres','atm']:
            pressure = self.p2  * 0.000986923
        elif units in ['psi']:
            pressure = self.p2  * 0.014503773773022
        elif units in ['Torr','mmHg']:
            pressure = self.p2  * 0.750062
        else:
            print('Units not valid. Defaulting to millibar.')
            pressure = self.p2 
        pressure = round(pressure,2)        
        return pressure
    

    def pressure(self, units='dbar',sea_level_pressure=1013.25,
                 resolution=8192):
        
        """Remove atmospheric pressure influence. 
        units -- units the user wants
        sea_level_pressure -- pressure exerted by atmosphere.
        resolution -- the resolution option of the sensor.
        """
        
        self.absolute_pressure() #Get the absolute pressure reading.
        p = self.abs_p - sea_level_pressure
        
        if p < 0:
            p = 0.00
        
        if units in ['millibar','mbar','hectopascals','hPa']:
            pressure = p
        elif units in ['decibar','dbar']:
            pressure = p / 100
        elif units in ['bar']:
            pressure = p /1000
        elif units in ['pascal','Pa']:
            pressure = p * 100
        elif units in ['kilopascals','kPa']:
            pressure = p / 10
        elif units in ['atmospheres','atm']:
            pressure = p * 0.000986923
        elif units in ['psi']:
            pressure = p * 0.014503773773022
        elif units in ['Torr','mmHg']:
            pressure = p * 0.750062
        else:
            print('Units not valid. Defaulting to decibar.')
            pressure = p / 100
        pressure = round(pressure,2)
        return pressure

 
    def depth(self,units='m',sea_level_pressure=1013.25, resolution=8192, 
              lat=45.00000, geo_strf_dyn_height=0, sea_surface_geopotential=0):
        
        """Compute depth using TEOS-10 and return depth in selected units.
        units -- units the user wants depth in
        sea_level_pressure -- pressure of atmosphere at sea level.
        resolution -- the resolution option of the sensor. 
        lat -- latitude of deployment, used in gsw_z_from_p (decimal degrees)
        geo_strf_dyn_height -- dynamic height anomaly  (m^2/s^2)
        sea_surface_geopotential -- geopotential at zero sea pressure (m^2/s^2)
        """
        
        p = self.pressure(units = 'dbar',
                          sea_level_pressure = sea_level_pressure,
                          resolution = resolution)
        z = self._gsw_z_from_p(p,lat,
                              geo_strf_dyn_height,sea_surface_geopotential)
        
        depth = self._gsw_depth_from_z(z)         
        
        if depth < 0:
            depth = 0.00
        
        if units in ['meters','m']:
            depth = depth
        elif units in ['feet','ft']:
            depth = depth * 3.28084
        elif units in ['fathoms','ftm']:
            depth = depth * 0.546807
        else:
            print('Units not valid. Defaulting to meters.')
            depth = depth     
        depth = round(depth,2)     
        return depth
    
    
    def _gsw_z_from_p(self,p,lat=45.00000,
                     geo_strf_dyn_height=0, 
                     sea_surface_geopotential=0):
        
        """Compute height using pressure.
        z = 0 is sea level. -z is going DOWN into the ocean.        
        p -- pressure in decibars
        lat -- latitude of deployment, used in gsw_z_from_p (decimal degrees)
        geo_strf_dyn_height -- dynamic height anomaly  (m^2/s^2)
        sea_surface_geopotential -- geopotential at zero sea pressure (m^2/s^2)        
        """
        
        gamma = 2.26e-7
        deg2rad = math.pi/180
        sinlat = math.sin(lat*deg2rad)
        sin2 = sinlat**2
        b = 9.780327*(1.0 + (5.2792e-3 + (2.32e-5*sin2))*sin2); 
        a = -0.5 * gamma * b
        c = (self._gsw_enthalpy_sso_0(p) 
            - (geo_strf_dyn_height 
            + sea_surface_geopotential))
        z = -2 * c / (b + math.sqrt(b * b - 4 * a *c))
        return z
        
     
    def _gsw_enthalpy_sso_0(self,p):
        
        """Compute enthalpy at Standard Ocean Salinity (SSO).  
        Assumes a Conservative Temperature of zero degrees Celsius.
        p -- pressure in decibars
        """
        
        z = p*1e-4
        h006 = -2.1078768810e-9
        h007 =  2.8019291329e-10
        dynamic_enthalpy_sso_0_p = (z * (9.726613854843870e-4 
                                        + z * (-2.252956605630465e-5 
                                        + z * (2.376909655387404e-6 
                                        + z * (-1.664294869986011e-7 
                                        + z * (-5.988108894465758e-9 
                                        + z * (h006 + h007*z)))))))
        enthalpy_sso_0 = dynamic_enthalpy_sso_0_p*1e8   
        return enthalpy_sso_0 
    
    
    def _gsw_depth_from_z(self,z):
        
        """Compute depth from height (z).
        z -- a negative z value denoting depth in the ocean.
        """        
        
        depth = -z
        return depth
    
    
    def altitude(self,units='m', sea_level_pressure=1013.25,
                 resolution=8192):
        
        """Compute altitude from atmospheric pressure.
        Pulled from original Blue Robotics MS5837 Python class.
        
        units -- units the user wants depth in
        sea_level_pressure -- pressure of atmosphere at sea level.
        resolution -- the resolution option of the sensor.         
        
        Future addition? Use metpy computation.
        """
        
        self.absolute_pressure()
        p = self.abs_p
        
        h =  (1-pow((p/sea_level_pressure),0.190284))*145366.45*.3048          
        if h < 0:
            h = 0.00
            print('If you are in the ocean, try the depth function.')
            print('Or try setting sea_level_pressure to your sensor reading.')
		
        if units in ['meters','m']:
            altitude = h
        elif units in ['feet','ft']:
            altitude = h * 3.28084
        else:
            print('Units not valid. Defaulting to meters.')
            altitude = h 
        altitude = round(altitude,2)
        return altitude
        


        
        