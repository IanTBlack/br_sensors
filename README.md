# br_sensors
A set of Python 3 modules for accessing Blue Robotics sensors.


## examples
This folder contains examples for driving each sensor or combination of sensors.
In order for them to work properly, you'll need to add each module to your Python path.
Alternatively, you could copy each class into your operating script.

## ms5837.py
This module contains a class for driving the MS5837-02BA or MS5837-30BA pressure sensor from Blue Robotics.
For an example that showcases the functions, go to examples > example_ms5837.py.

There are seven main functions.

initialize_sensor() <- Sets up the sensor and gets the calibration coeffiencents. Must be called before requesting data.
temperature() <- Gets the temperature from the pressure sensor.
absolute_pressure() <- Gets the absolute pressure (water column + atmosphere) in defined units.
pressure() <- Removes atmosphere and gets the pressure exerted by the water column in defined units..
depth() <- Computes depth from pressure in defined units.
altitude() <- Computes altitude from absolute pressure in defined units.
reset_sensor() <- Can be called if there is a read error from the sensor memory.



## tsys01.py
This module contains a class for driving the TSYS01 temperature sensor from Blue Robotics.
For an example that showcases the functions, go to examples > example_tsys01.py.

There are four main functions.

initialize_sensor() <- Sets up the sensor and gets the calibration coeffiencents. Must be called before requesting data.
temperature() <- Gets the temperature from the temperature sensor.
burst_avg_temperature() <- Rapidly takes X samples, drops the first and last values, and averages the rest.
sn() <- Gets the sensor serial number.
reset_sensor() <- Can be called if there is a read error from the sensor memory.