"""
The main function creates a LSL stream including one or more data types (e.g. 
accelleration, orientation, etc.) from one or more Yost 3Space Mini Wirelees IMU 
sensors connected to the PC via a wireless dongle.
This script must be located in the same folder as ThreeSpaceAPI.py. That folder
must contain a subfolder named exampleComClasses and containing the script USB_ExampleClass.py 


Connect 3-Space Dongle to PC using usb cable and urn on the wireless sensor(s). 
Dongle and sensors must be already paired. This is done via the 3-Space suite program 
avialable here:
    https://yostlabs.com/yost-labs-3-space-sensor-software-suite/
The steps to do that are described in the 3-Space suite documentation avialable here:
    https://yostlabs.com/wp-content/uploads/pdf/3-Space-Sensor-Suite-Manual.pdf

"""
from pylsl import StreamInfo, StreamOutlet
import getopt
import sys
from exampleComClasses import USB_ExampleClass
from ThreeSpaceAPI import ThreeSpaceSensor, STREAM_CONTINUOUSLY, Streamable
import time
import numpy as np
from ThreeSpaceAPI import _streamingCommands
import re

# helper functions
def computeStreaminLen(sens,logicalID=0):
    '''
    get the number of dimensions of a streaming packet

    Parameters
    ----------
    sens : sensor object
        sensor object permitting to acces the sensors to query.
    logicalID : int, optional
        ID of the sensor to query. The default is 0.

    Returns
    -------
    dimNum : integer
        number of dimensions returned by each straming packet.

    '''
    allSlots=sens.getStreamingSlots(logicalID=logicalID)
    allSlots=allSlots[5:]
    allSlots=[i for i in allSlots if i!=255]   
    dimNum=0
    for mySlot in allSlots:
        thisFormat=_streamingCommands[mySlot]
        Allvals=re.findall("\d{0,3}[fB]", thisFormat) # look for all occurrence of f or B preceded by 0,1,2 or 3 numbers
        Allvals=[int(i[:-1]) if len(i)>1 else 1  for i in Allvals ]#transfor into integers the numbers that precede teh seqs, if no num put 1
        dimNum+=sum(Allvals)# sum  the number of elements
    return dimNum


def initialize_sensor_streaming(comPortName,logicalIDs,content,srate ):
    '''
    Initialize data streaming from sensors. It computes the dimensionality of
    the data stream and the sampling rate given the selected slots. Moreover it
    tries launching the streaming several times until the received streaming packets
    are not empty. Indeed the first time streaming is launched after a dongle is 
    plugged in, streaming packets may come out empty. Normally at the second trial 
    it should work. If it doesen't after ten trials, an exception is thrown.

    Parameters
    ----------
    comPortName : str
        Name of the COM port to be used.
    logicalIDs : list of integers
        IDs of the sensors to be used.
    content : list of strings
        names of the required streaming variables.
    srate : float
        desired sampling rate.

    Returns
    -------
    com : obj
        comunication object.
    sensor : TYPE
        sensor object.
    n_channels : TYPE
        number of channels to stream.
    nominal_sr : TYPE
        achieved sr.

    '''
    success=0
    nTrials=0
    while (success==0) & (nTrials<10):
        nTrials+=1
        # Create communication object instance.
        com = USB_ExampleClass.UsbCom(portName=comPortName,timeout=0.05)
        # Create sensor instance. This will call the open function of the communication object
        # and set our buffer length to desired length.
        sensor = ThreeSpaceSensor(com,streamingBufferLen=1000)
        
        dataLens=[]
        
        
        for thisID in logicalIDs:
            # Set sensor to stream required variables
            sensor.setStreamingSlots(*[eval('Streamable.'+ s) for s in content],logicalID=thisID)
            
            dataLens.append(computeStreaminLen(sensor,logicalID=thisID))
            
        n_channels=np.sum(dataLens)
        
        sensor.setResponseHeaderBitfield(0x53)
        for thisID in logicalIDs:
            # Set sensor to stream at 100Hz for specified number of seconds with no start delay, all arguments are in microseconds
            sensor.setStreamingTiming(0,STREAM_CONTINUOUSLY ,0 ,logicalID=thisID)
            sensor.clearStreamingBuffer(logicalID=thisID)
        
        if nTrials==1:
            print("Trying to Start Streaming")
        else:            
            print("Trying to Start Streaming again")
            
        for thisID in logicalIDs:
            sensor.startStreaming(logicalID=thisID)
        
        data = [None]*len(logicalIDs)
        deltaTs=[]
        t0=time.perf_counter_ns()
        nPacketsReceived=0
        nEmptyPackets=0
        while (nPacketsReceived<50) & (nEmptyPackets<50):
            # Streamed data is added to buffer. This method safely accesses that buffer
            for thisID in logicalIDs:
                data[thisID] = sensor.getOldestStreamingPacket(logicalID=thisID)
         
            if None in data :# if one of the packet retrived is none
                # allow the streaming thread time to fill the streaming buffer
                time.sleep(1/srate)
                nEmptyPackets+=1
            else:
                t1=time.perf_counter_ns()
                deltaTs.append((t1-t0)/1000000000)
                t0=t1
                nPacketsReceived+=1
                success=1
        for thisID in logicalIDs:
             sensor.stopStreaming(logicalID=thisID)
        
        if success==0:
           #Y close communication object
           sensor.cleanup()
           com=None
           sensor=None
           nominal_sr=np.nan
        else:
           nominal_sr=1/np.nanmean(deltaTs)
    
    return com, sensor, n_channels, nominal_sr

def hertzToInterval(hertz):
    # convert an frequency in Hertz into the duration of the corresponding interval in microsecs
    return int(1000000/hertz)
    
def main(argv):
    '''
    Launch sensors streaming and broadcast the stream toward LAb Streaming Layer 

    Parameters
    ----------
    srate : int, optional
        streaming rate required to the sensors in frames per secs. Default: 100
    
    lslRate: int, optional
        streaming rate declared to Lab Streaming Layer. If none srate is used. Default: None
    
    name: str, optional. Default: 'YostSens'
        streaming name
        
    comPortName: str, optional. Default: 'COM10'
        name of the COM port
        
    logicalIDs: list of integers>=0 and <=15, optional. Default: [0,1]: IDs of the sensor to stream
        
    content: list of (max 8) strings, streaming variables  
        
    typeStreaming: str, optional. Default: 'EEG'
        type of streaming declared to Lab Streaming Layer
    
    Returns
    -------
    None.

    '''
    srate=100
    lslRate=None
    comPortName='COM10'
    name = 'YostSens'
    typeStreaming = 'IMUs'
    logicalIDs = [0,1]
    content = ['READ_TARED_ORIENTATION_AS_MAT' , 
               'READ_TARED_ORIENTATION_AS_AXIS_ANGLE' ,
               'READ_TARED_ORIENTATION_AS_EULER' ]
        
    
    help_string = 'SendData.py -s <sampling_rate> -m <lsl_rate> -n <stream_name> -p <port_name> -c <stream_content> -l <sensors_IDs> -t <stream_type>'
        
    try:
        opts, args = getopt.getopt(argv, "hs:l:n:p:l:c:t:", longopts=["srate=", "lslRate=","name=", "port=","logicalIDs=","content=", "type"])
    except getopt.GetoptError:
        print(help_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(help_string)
            sys.exit()
        elif opt in ("-s", "--srate"):
            srate = float(arg)
        elif opt in ("-l", "--lslRate"):
             lslRate = float(arg)
        elif opt in ("-n", "--name"):
            name = arg
        elif opt in ("-p", "--port"):
            comPortName = arg    
        elif opt in ("-l", "--logicalIDs"):
            logicalIDs = arg    
        elif opt in ("-c", "--content"):
            content = arg
        elif opt in ("-t", "--typestream"):
            typeStreaming = arg
        
    [com, sensor, n_channels, realRate]=initialize_sensor_streaming(comPortName,
                                        logicalIDs,content,srate )
    print("Streaming initialized, nominal rate: "+str(lslRate))
    
    if com is None:
        raise Exception('Unable to initialize streaming')
    
    # Define LSL streaming info
    if lslRate==None:
         info = StreamInfo(name, typeStreaming, int(n_channels), np.floor(realRate), 'float32', 'myuid34234')
    else:
         info = StreamInfo(name, typeStreaming, n_channels, lslRate, 'float32', 'myuid34234')
    
    # create a LSL outlet
    outlet = StreamOutlet(info)
 
    sensor.setResponseHeaderBitfield(0x53)
    for thisID in logicalIDs:
        sensor.clearStreamingBuffer(logicalID=thisID)
    
    # start streaming from sensors
    for thisID in logicalIDs:
        sensor.startStreaming(logicalID=thisID)
    print("Streaming started!")

    data = [None]*len(logicalIDs)
    deltaTs=[]
    t0=time.perf_counter_ns()
    try:
        while True:
            # retrive data from sensors' buffers
            for thisID in logicalIDs:
                data[thisID] = sensor.getOldestStreamingPacket(logicalID=thisID)
         
            if None in data :# if one of the packet retrived is none
                # allow the streaming thread time to fill the streaming buffer
                time.sleep(1/srate)
            else:
                dataOut=[ii for sub in data for ii in sub[5:]]
                outlet.push_sample(dataOut,np.array(data[0][1:2])/1000000)
                t1=time.perf_counter_ns()
                deltaTs.append((t1-t0)/1000000000)
                t0=t1
                
                
    except KeyboardInterrupt:
        
            for thisID in logicalIDs:
                sensor.stopStreaming(logicalID=thisID)
        
            #Y close communication object and join any spawned threads
            sensor.cleanup()
    
            print("Done!")
            print(1/np.nanmean(deltaTs))

if __name__ == '__main__':
    main(sys.argv[1:])