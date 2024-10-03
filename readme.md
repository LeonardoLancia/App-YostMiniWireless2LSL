# App-YostMiniWireless2LSL

Simple code to create a LSL stream including one or more data types (e.g. accelleration, orientation, etc.) from one or more Yost 3Space Mini Wirelees IMU sensors connected to the PC via a wireless dongle.

Before launching the streaming the scripts performs several initialization operations:

1) The first time streaming is launched after a dongle has been plugged in, streaming packets may come out empty. Therefore, the scripts tries to intialize the COM port and the sensors and launch the stream several times. Each time checking if the streamed packets are empty. 
Usually two trials are enough to get data, however if after 10 trials the pakets are empty an exception is thrown. 

2) During this check the time lag between consecutive non empty packets of data is used to estimate the actual sampling rate avialable with the number of sensors and the data required.

3) Finally the number of LSL streaming channels is computed based on the number of sensors and the queries sent to the sensors.

After these initialization steps, the stream is launched and is interrupted only when the window in which the code is running is under focus and the user presses CTRL+C.

## Installation and requirements:
You need to download and unpack the Yost 3Space sensor API for Python 3 which is avialable here:

https://yostlabs.com/wp-content/uploads/2023/04/ThreeSpaceAPI_py3_beta_V0.6.zip

Copy the script **yost3sLSL.py** from this reposirtory to same folder as **ThreeSpaceAPI.py** included in the Yost 3Space sensor API

The following python modules should also be installed:

pylsl

numpy

## Usage:
This is a command line scripts that acceps the following parameters: 

**srate** (int, optional): streaming rate required to the sensors in frames per secs. Default: 100
    
**lslRate** (int, optional; Default: None): streaming rate declared to Lab Streaming Layer. If none, the declared sampling rate is estimated by measuring the lag between the storage of consecutive packets during the initialization step.
    
**name** (int, optional; Default: 'YostSens'): streaming name
        
**comPortName** (str, optional; Default: 'COM10'): name of the COM port

**logicalIDs** (list of int >=0 and <=15, optional. Default: [0,1]): IDs of the sensor(s) to stream
        
**content** (list of (max 8) strings, optional; Default: ['READ_TARED_ORIENTATION_AS_MAT','READ_TARED_ORIENTATION_AS_AXIS_ANGLE' ,'READ_TARED_ORIENTATION_AS_EULER' ]): 
	streaming variables  

**typeStreaming** (str, optional; Default: 'IMU'): type of streaming declared to Lab Streaming Layer

## Examples:
from the command line 

**python yost3sLSL -s 90**

from IPython console:

**%run yost3sLSL -s 90**