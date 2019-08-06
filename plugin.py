# Domoticz-GPIO-Plugin
#
# Author: Dnpwwo
#
#
"""
<plugin key="RPiGPIO" name="Raspberry Pi GPIO" author="dnpwwo" version="1.0.0" wikilink="https://github.com/dnpwwo/Domoticz-GPIO-Plugin" >
    <description>
        <h2>Domoticz GPIO Plugin</h2><br/>
        <h3>Configuration</h3>
        <ul style="list-style-type:square">
            <li style="line-height:normal">Output Pins - Comma delimited list of output (relay) pins. Format is pin number colon NO or NC (e.g 39:NO)</li>
            <li style="line-height:normal">Input Pins - Comma delimited list of board pin numbers (1-40) to check for input</li>
            <li style="line-height:normal">Switch Debounce - Time (ms) between valid switch presses, prevents multi reports of events</li>
            <li style="line-height:normal">Heartbeat Frequency - Determines how often Input Pins are checked for values</li>
            <li style="line-height:normal">Debug - When true the logging level will be much higher to aid with troubleshooting</li>
        </ul>
    </description>
    <params>
        <param field="Mode1" label="Output Pins" width="400px"/>
        <param field="Mode2" label="Input Pins" width="300px"/>
        <param field="Mode3" label="Switch Debounce" width="50px">
            <options>
                <option label="50" value="50"/>
                <option label="100" value="100"/>
                <option label="150" value="150"/>
                <option label="200" value="200" default="true" />
                <option label="250" value="250"/>
            </options>
        </param>
        <param field="Mode5" label="Heartbeat Frequency" width="50px">
            <options>
                <option label="1" value="1"/>
                <option label="2" value="2"/>
                <option label="3" value="3"/>
                <option label="4" value="4"/>
                <option label="5" value="5"/>
                <option label="6" value="6"/>
                <option label="8" value="8"/>
                <option label="10" value="10" default="true" />
                <option label="12" value="12"/>
                <option label="14" value="14"/>
                <option label="16" value="16"/>
                <option label="18" value="18"/>
                <option label="20" value="20"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Event Queue" value="128"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import RPi.GPIO as GPIO

def onStart():
    if Parameters["Mode6"] != "0":
        Domoticz.Log("Parameter is: '"+Parameters["Mode6"]+"'")
        Domoticz.Debugging(int(Parameters["Mode6"]))
        DumpConfigToLog()

    GPIO.setmode(GPIO.BOARD)
    Domoticz.Heartbeat(int(Parameters["Mode5"]))
    Domoticz.Log("RPi.GPIO imported, Version: "+str(GPIO.VERSION)+", Raspberry Pi board revision: "+str(GPIO.RPI_INFO['P1_REVISION']))
    
    # Process Output Pins
    if (len(Parameters["Mode1"]) > 0):
        try:
            outputPins = Parameters["Mode1"].split(',')
            for pin in outputPins:
                items = pin.split(':')
                pinNo = int(items[0])
                if not (pinNo in Devices):
                    Domoticz.Log("Creating Output device #"+items[0])
                    Domoticz.Device(Name="Output "+items[0], Unit=pinNo, TypeName="Push Off" if items[1] == "NC" else "Push On").Create()
                GPIO.setup(pinNo, GPIO.OUT, initial=GPIO.HIGH if items[1] == "NC" else GPIO.LOW)
                UpdateDevice(pinNo, GPIO.input(pinNo), "", 0)
        except Exception as inst:
            Domoticz.Error("Exception in onStart, processing Output Pins")
            Domoticz.Error("Exception detail: '"+str(inst)+"'")
            raise

    # Process Input Pins
    if (len(Parameters["Mode2"]) > 0):
        try:
            inputPins = Parameters["Mode2"].split(',')
            for pin in inputPins:
                pinNo = int(pin)
                if not (pinNo in Devices):
                    Domoticz.Log("Creating Input device #"+pin)
                    Domoticz.Device(Name="Input "+pin, Unit=pinNo, TypeName="Contact").Create()
                GPIO.setup(pinNo, GPIO.IN)
                GPIO.add_event_detect(pinNo, GPIO.BOTH, callback=gpioCallback, bouncetime=int(Parameters["Mode3"]))
                UpdateDevice(pinNo, GPIO.input(pinNo), "", 0)
        except Exception as inst:
            Domoticz.Error("Exception in onStart, processing Input Pins")
            Domoticz.Error("Exception detail: '"+str(inst)+"'")
            raise

def gpioCallback(channel):
    channelValue = GPIO.input(channel)
    Domoticz.Debug("gpioCallback called, Channel: "+str(channel)+", Value: "+str(channelValue))
    UpdateDevice(channel, channelValue, "On" if channelValue == GPIO.HIGH else "Off", 0)

def onCommand(Unit, Command, Level, Hue):
    Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
    GPIO.output(Unit, GPIO.HIGH if Command == "On" else GPIO.LOW)
    UpdateDevice(Unit, GPIO.input(Unit), Command, 0)

def onStop():
    Domoticz.Debug("onStop called")
    GPIO.cleanup()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Log("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Log("Device LastLevel: " + str(Devices[x].LastLevel))
    return
    
def UpdateDevice(Unit, nValue, sValue, TimedOut):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].TimedOut != TimedOut):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue), TimedOut=TimedOut)
            Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return
