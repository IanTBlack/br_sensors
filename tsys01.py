"""
#Tested on a Raspberry Pi 4.
#Tested in Python 3.7.3 via Spyder 3.3.3.

#Description
    A class for operating the TSYS01 over I2C on a Raspberry Pi.
    
    Temperature is calculated per the TE TSYS01 manual.
    https://www.te.com/commerce/DocumentDelivery/DDEController?Action=showdoc&DocId=Data+Sheet%7FTSYS01%7FA%7Fpdf%7FEnglish%7FENG_DS_TSYS01_A.pdf%7FG-NICO-018
    
#Pinouts for Blue Robotics TSYS01 Series
    TSYS01 - RPi
    Red - 3.3v
    Black - GND
    Green - SCL
    White - SDA
    
#Example
    tsys01 = TSYS01()  #Set up class for a MS5837-30BA sensor.
    tsys01.initialize_sensor()  #Initialize the sensor.
    
    #Get temperature in Celsius.
    
    temperature = tsys01.temperature('Celsius') 
"""


try:  
    import time  #Used for pausing.
    import smbus  #Used for I2C comms with TSYS01.
except ImportError: 
    print("The smbus module is required.")
    print("Try 'sudo apt-get install python-smbus' in Terminal.")
   
    
class TSYS01():
    def __init__(self,bus = 1,address = 0x77): #Run at class instantiation.
        self._reset = 0x1E  #Command to reset the sensor.
        self._convert = 0x48  #Command to compute adc.
        self._read = 0x00  #Command to read adc computation response.
        self._prom = [0xAA,0xA8,0xA6,0xA4,0xA2] #Order: k0,k1,k2,k3,k4
        self._bus = bus
        self._address = address
        if self._address in [0x76,0x77]:
            try:  
                self._i2c = smbus.SMBus(self._bus) #Try to set up an I2C object. 
            except: 
                print("Can't initiate I2C over bus #{}.".format(self._bus))
                print("1) Do you have python-smbus installed?")
                print("2) Check device status with 'i2cdetect -y 1'")
                print("\tor 'i2cdetect -y 0' via Terminal.")
                print("3) Check SDA/SCL orientation.")
        else:
            print('Address must be 0x77 or 0x76.')
            
        
    def initialize_sensor(self): #Reset sensor and get cal coeffs.
        self.reset_sensor()
        self._calibration_data() 
        return True
     
        
    def _calibration_data(self): #Function that gathers k0,k1,k2,k3, and k4.
        self._cal_data = [] #Holder for calibration coefficients.
        for k in self._prom: #For each PROM read command...
            word = self._i2c.read_word_data(self._address,k) #Request coeff.       
            coeff = ((word & 0xFF) << 8) | (word >> 8) 
            self._cal_data.append(coeff) #Append to previous for loop.
            
      
    def _read_adc(self): #Get the 24 bit ADC conversion reading.
        try: #Check to see if the I2C object has been made.
            self._i2c
        except: 
            print("Unable to initiate I2C over bus #{}.".format(self._bus))
        self._i2c.write_byte(self._address,self._convert) #ADC conversion.
        time.sleep(0.01) 
        adc24 = self._i2c.read_i2c_block_data(self._address,self._read,3) 
        self._adc24 = adc24[0] << 16 | adc24[1] << 8 | adc24[2] 


    def _adc2temp(self):  
        k0 = self._cal_data[0]
        k1 = self._cal_data[1]
        k2 = self._cal_data[2]
        k3 = self._cal_data[3]
        k4 = self._cal_data[4]      
        adc16 = self._adc24/256
        self._t = (-2 * k4 * 10**-21 * adc16**4  
                  + 4  * k3 * 10**-16 * adc16**3 
                  + -2 * k2 * 10**-11 * adc16**2 
                  + 1  * k1 * 10**-6  * adc16 
                  + -1.5 * k0 * 10**-2)        
    
    
    def temperature(self, units = 'degC'):
        self._read_adc()
        self._adc2temp()
        if units in ['Celsius' , 'degC','C']:
            temperature  = self._t
        elif units in ['Fahrenheit' , 'degF' , 'F']:
            temperature = 1.8 * self._t + 32
        elif units in ['Kelvin' , 'degK' , 'K']:
            temperature = self._t + 273.15   
        else:
            print('Units not valid. Defaulting to Celsius.')
            temperature = self._t
        self._temperature_float = temperature #Assigned for use in b_a_t.
        temperature = round(temperature,2)    
        return temperature
    
    
    def sn(self):
        data_23_8 = self._i2c.read_word_data(self._address,0xAC)
        sn_23_8 = ((data_23_8  & 0xFF) << 8) | (data_23_8  >> 8) 
        data_7_0 = self._i2c.read_word_data(self._address,0xAE)
        sn_7_0 = (data_7_0 >> 8)     
        serial_number = (2**8) * sn_23_8 + sn_7_0 #Compute the serial number.
        return serial_number


    def reset_sensor(self): 
        self._i2c.write_byte(self._address,self._reset)
        time.sleep(0.01)  #Reset only takes 2.8ms, but wait for 10ms.
        return True
        
    
    
    #-----EXPERIMENTAL-----#       
    def burst_avg_temperature(self,number_samples = 10,units = 'degC'):
        
       
        #Restrict number_samples to reduce influence of self heating.
        if number_samples >= 11:
            number_samples = 10 
        else:
            number_samples = number_samples
        t_array = []
        for i in range(number_samples):
            self.temperature(units=units)
            t = self._temperature_float
            t_array.append(t)
        t_array = t_array[1:len(t_array)-1] #Drop the first and last values.
        burst_avg = sum(t_array)/len(t_array) #Average the remaining.
        burst_avg = round(burst_avg,2)
        return burst_avg
