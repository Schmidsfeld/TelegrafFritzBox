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

# print out connection type and device information
deviceInfo = readfritz('DeviceInfo1', 'GetInfo')
firmware = 'Firmware="'+ fc.device_manager.system_version+'"'
model = extractvar(deviceInfo, 'NewModelName', False)
print('The current active device is')
print(model+firmware)
print()

connectionType = readfritz('Layer3Forwarding', 'GetDefaultConnectionService')
print('Connection Type is:')
print(connectionType)
print()
connection = str(connectionType['NewDefaultConnectionService'])
connection = connection.replace("1.","")
connection = connection.replace(".","")
availStats= readfritz(connection, 'GetInfo')
print('Available Stats are:')
print(availStats)
