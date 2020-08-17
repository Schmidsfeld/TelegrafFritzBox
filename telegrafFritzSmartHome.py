#!/opt/bin/python3

# This script is for exporting FritzBox metrics into Telegraf in InfluxDB format.
# https://github.com/Schmidsfeld/TelegrafFritzBox
# License: MIT (https://opensource.org/licenses/MIT)
# Author: Alexander von Schmidsfeld

# This script requires the FritzConnection package
# Install with:
# pip3 install fritzconnection

from fritzconnection import FritzConnection
from fritzconnection.cli.utils import get_cli_arguments
import sys
import itertools


FRITZBOX_ID = 'FritzBoxSmartHome' # Name of the InfluxDB database.


# This script uses optionally the environment variables for authentification:
# FRITZ_IP_ADDRESS  IP-address of the FritzBox (Default 169.254.1.1)
# FRITZ_TCP_PORT    Port of the FritzBox (Default: 49000)
# FRITZ_USERNAME    Fritzbox authentication username (Default: Admin)
# FRITZ_PASSWORD    Fritzbox authentication password


# Helper modules for extracting and parsing variables
def readfritz(module, action):
    try:
        answer = fc.call_action(module, action)
    except:
        answer = dict() # return an empty dict in case of failure
    return answer

def extractvar(answer, variable, integer=False, string=True, name=""):
    if variable in answer.keys():
        avar = str(answer[variable])
        avar = avar.replace('"','')
        if name == "":
            name = variable
        if integer:
            avar = name + '=' + avar +'i' # format for integers in influxDB
        else:
            if string:
                avar = name + '="' + avar +'"' # format for strings in influxDB
            else:
                avar = name + '=' + avar # format for float/double in influxDB
    else:
        avar = ''
    return avar

def assemblevar(*args):
    data = ','.join(list(args))+','
    #cleaning up output
    data = data.replace("New", "")
    data = data.replace(",,",",")
    data = data.replace(",,",",")
    data = data.replace(",,",",")
    data = data.replace(",,",",")
    data = data[:-1]
    return data

def influxrow(tag, data):
    influx = FRITZBOX_ID + ',source=' + tag + ' ' + data
    print(influx)

# Connect to the FritzBox
args = get_cli_arguments()
if not args.password:
    print('Password required.')
    print()
    print('Options:')
    print('-i [ADDRESS],  IP-address of the FritzBox (Default 169.254.1.1)')
    print('-p [PASSWORD], Fritzbox authentication password')
    print('-u [USERNAME], Fritzbox authentication username (Default: Admin)')
    print('--port [PORT], Port of the FritzBox (Default: 49000)')
    print('-e [ENCRYPT],  use secure connection (Default: Off)')
    print()
    print('Hint: if this script is not working often IP or password is missing')
    sys.exit(1)
else:
    try:
        #fc = FritzConnection(args) # Dosn't seem to work dirctly
        fc = FritzConnection(address=args.address, user=args.username, password=args.password, port=args.port, timeout=2.0)
    except BaseException:
        print(BaseException)
        print("Cannot connect to fritzbox. ")
        print()
        print('Options:')
        print('-i [ADDRESS],  IP-address of the FritzBox (Default 169.254.1.1)')
        print('-p [PASSWORD], Fritzbox authentication password')
        print('-u [USERNAME], Fritzbox authentication username (Default: Admin)')
        print('--port [PORT], Port of the FritzBox (Default: 49000)')
        print('-e [ENCRYPT],  Use secure connection (Default: Off)')
        print()
        print('Hint: if this script is not working often IP or password is missing')
        sys.exit(1)

# Iterate over all known smarthome device and generate one influxDB line per device 
for n in itertools.count():
    try:
        #device = self.get_device_information_by_index(n)
        #return self._action('GetGenericDeviceInfos', NewIndex=n)
        device = fc.call_action('X_AVM-DE_Homeauto1', 'GetGenericDeviceInfos', NewIndex=n)
    except IndexError:
        break
    name = extractvar(device, 'NewDeviceName', False, False)
    name = name.replace('NewDeviceName=','') 
    power = extractvar(device, 'NewMultimeterPower', True, False, 'Power') # Power currently consumed in W *100
    energy = extractvar(device, 'NewMultimeterEnergy', True, False, 'Energy') # Energy consumed in Wh
    temperature = extractvar(device, 'NewTemperatureCelsius', True, False, 'Temperature') # Temperature in celcius * 10
    homeDevice = assemblevar(power, energy, temperature)
    influxrow(name, homeDevice)
