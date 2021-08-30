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


FRITZBOX_ID = 'FritzBox' # Name of the InfluxDB database.
IS_DSL = True # Switch to False for Cable or IP Connections
IS_INTERNET_FACING = True # Switch to False, if your Fritzbox used non public ip


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
    influx = FRITZBOX_ID +','+ fbName +  ',source=' + tag + ' ' + data
    print(influx)

# Speccialist Stats that have to be assembled (counted) ourselfes
def gethosts():
    hostsKnown = 0
    hostsActive = 0
    lanHostsActive = 0
    wlanHostsActive = 0
    lanHosts = 0
    wlanHosts = 0
    for n in itertools.count():
        try:
            host = fc.call_action('Hosts1', 'GetGenericHostEntry', NewIndex=n)
        except IndexError:
            break
        hostsKnown = hostsKnown +1
        if host['NewActive']:
            hostsActive = hostsActive +1
            if host['NewInterfaceType'] == 'Ethernet': lanHostsActive = lanHostsActive +1
            if host['NewInterfaceType'] == '802.11': wlanHostsActive = wlanHostsActive +1
        if host['NewInterfaceType'] == 'Ethernet': lanHosts = lanHosts +1
        if host['NewInterfaceType'] == '802.11': wlanHosts = wlanHosts +1
    hosts = {'HostsKnown':hostsKnown, 'HostsActive':hostsActive, 'HostsKnownLAN':lanHosts, 'HostsActiveLAN':lanHostsActive, 'HostsKnownWLAN':wlanHosts, 'HostsActiveWLAN':wlanHostsActive,}
    return hosts


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


# Get FritzBox data so it isn't requested mutiple times
deviceInfo = readfritz('DeviceInfo1', 'GetInfo')
if IS_DSL:
    connectionInfo = readfritz('WANPPPConnection1', 'GetInfo')
else:
    connectionInfo = readfritz('WANIPConn1', 'GetStatusInfo')
wanInfo = readfritz('WANCommonIFC1', 'GetCommonLinkProperties')
trafficInfo = readfritz('WANCommonIFC1', 'GetAddonInfos')
dslInfo = readfritz('WANDSLInterfaceConfig1', 'GetInfo')
dslError = readfritz('WANDSLInterfaceConfig1', 'GetStatisticsTotal')
fritzInfo = readfritz('LANHostConfigManagement1', 'GetInfo')
dhcpInfo = readfritz('Hosts1', 'GetHostNumberOfEntries')
hostInfo = gethosts()
lanStat = readfritz('LANEthernetInterfaceConfig1', 'GetStatistics')
wlanStat24 = readfritz('WLANConfiguration1', 'GetStatistics')
wlanStat50 = readfritz('WLANConfiguration2', 'GetStatistics')
wlanStatGuest = readfritz('WLANConfiguration3', 'GetStatistics')
wlanInfo24 = readfritz('WLANConfiguration1', 'GetInfo')
wlanInfo50 = readfritz('WLANConfiguration2', 'GetInfo')
wlanInfoGuest = readfritz('WLANConfiguration3', 'GetInfo')
wlanAssoc24 = readfritz('WLANConfiguration1', 'GetTotalAssociations')
wlanAssoc50 = readfritz('WLANConfiguration2', 'GetTotalAssociations')
wlanAssocGuest = readfritz('WLANConfiguration3', 'GetTotalAssociations')


# Parse single variables into influxdb compatible strings

# General Fritzbox information
firmware = 'Firmware="'+ fc.device_manager.system_version+'"'
model = extractvar(deviceInfo, 'NewModelName', False)
serial = extractvar(deviceInfo, 'NewSerialNumber', False)
fbName = extractvar(fritzInfo, 'NewDomainName', False, False, 'host')

# Connection Information
upTime = extractvar(deviceInfo, 'NewUpTime', True)
connectionTime = extractvar(connectionInfo, 'NewUptime', True, False, 'ConnectionTime')
connectionStatus = extractvar(connectionInfo, 'NewConnectionStatus', False)
connectionError = extractvar(connectionInfo, 'NewLastConnectionError', False, True, 'LastError')
connectionType = extractvar(wanInfo, 'NewWANAccessType', False, True)
maxDownRate = extractvar(wanInfo, 'NewLayer1DownstreamMaxBitRate', True)
maxUpRate = extractvar(wanInfo, 'NewLayer1UpstreamMaxBitRate', True)

# Traffic information
downRate = extractvar(trafficInfo, 'NewByteReceiveRate', True)
upRate = extractvar(trafficInfo, 'NewByteSendRate', True)
downPackageRate = extractvar(trafficInfo, 'NewPacketReceiveRate', True)
upPackageRate = extractvar(trafficInfo, 'NewPacketSendRate', True)
#downTotal = extractvar(trafficInfo, 'NewTotalBytesReceived', True) #depreciated since 64bit is more usefull
#upTotal = extractvar(trafficInfo, 'NewTotalBytesSent', True) #depreciated since 64bit is more usefull
downTotal64 = extractvar(trafficInfo, 'NewX_AVM_DE_TotalBytesReceived64', False, False, 'TotalBytesReceived64' )
upTotal64 = extractvar(trafficInfo, 'NewX_AVM_DE_TotalBytesSent64', False, False, 'TotalBytesSent64')

# Network Information
externalIP = extractvar(connectionInfo, 'NewExternalIPAddress', False )
dns = extractvar(connectionInfo, 'NewDNSServers', False)
localDns = extractvar(fritzInfo, 'NewDNSServers', False, True, 'LocalDNSServer')
hostsEntry = extractvar(dhcpInfo, 'NewHostNumberOfEntries', True)
hostsKnown = extractvar(hostInfo, 'HostsKnown', True)
hostsKnownLAN = extractvar(hostInfo, 'HostsKnownLAN', True)
hostsKnownWLAN = extractvar(hostInfo, 'HostsKnownWLAN', True)
hostsActive = extractvar(hostInfo, 'HostsActive', True)
hostsActiveLAN = extractvar(hostInfo, 'HostsActiveLAN', True)
hostsActiveWLAN = extractvar(hostInfo, 'HostsActiveWLAN', True)

# DSL specific input
if IS_DSL:
    dslDown = extractvar(dslInfo, 'NewDownstreamCurrRate', True)
    dslUp = extractvar(dslInfo, 'NewUpstreamCurrRate', True)
    dslMaxDown = extractvar(dslInfo, 'NewDownstreamMaxRate', True)
    dslMaxUp = extractvar(dslInfo, 'NewUpstreamMaxRate', True)
    noiseDown = extractvar(dslInfo, 'NewDownstreamNoiseMargin', True)
    noiseUp = extractvar(dslInfo, 'NewUpstreamNoiseMargin', True)
    powerDown = extractvar(dslInfo, 'NewDownstreamPower', True)
    powerUp = extractvar(dslInfo, 'NewUpstreamPower', True)
    attenuationDown = extractvar(dslInfo, 'NewDownstreamAttenuation', True)
    attenuationUp = extractvar(dslInfo, 'NewUpstreamAttenuation', True)
    fecError = extractvar(dslError, 'NewFECErrors', True)
    fecErrorLocal = extractvar(dslError, 'NewATUCFECErrors', True)
    crcError = extractvar(dslError, 'NewCRCErrors', True)
    crcErrorLocal = extractvar(dslError, 'NewATUCCRCErrors', True)
    hecError = extractvar(dslError, 'NewHECErrors', True)
    hecErrorLocal = extractvar(dslError, 'NewATUCHECErrors', True)

# Local network Statistics
lanPackageUp = extractvar(lanStat, 'NewPacketsSent', True)
lanPackageDown = extractvar(lanStat, 'NewPacketsReceived', True)
wlanPackageUp24 = extractvar(wlanStat24, 'NewTotalPacketsSent', True, False, 'PacketsSent' )
wlanPackageDown24 = extractvar(wlanStat24, 'NewTotalPacketsReceived', True, False, 'PacketsReceived')
wlanPackageUp50 = extractvar(wlanStat50, 'NewTotalPacketsSent', True, False, 'PacketsSent')
wlanPackageDown50 = extractvar(wlanStat50, 'NewTotalPacketsReceived', True, False, 'PacketsReceived')
wlanPackageUpGuest = extractvar(wlanStatGuest, 'NewTotalPacketsSent', True, False, 'PacketsSent')
wlanPackageDownGuest = extractvar(wlanStatGuest, 'NewTotalPacketsReceived', True, False, 'PacketsReceived')
wlanName24 = extractvar(wlanInfo24, 'NewSSID', False)
wlanName50 = extractvar(wlanInfo50, 'NewSSID', False) 
wlanNameGuest = extractvar(wlanInfoGuest, 'NewSSID', False) 
wlanChannel24 = extractvar(wlanInfo24, 'NewChannel', True)
wlanChannel50 = extractvar(wlanInfo50, 'NewChannel', True)
wlanChannelGuest = extractvar(wlanInfoGuest, 'NewChannel', True)
wlanClients24 = extractvar(wlanAssoc24, 'NewTotalAssociations', True, False, 'ClientsNumber')
wlanClients50 = extractvar(wlanAssoc50, 'NewTotalAssociations', True, False, 'ClientsNumber')
wlanClientsGuest = extractvar(wlanAssocGuest, 'NewTotalAssociations', True, False, 'ClientsNumber')


# Output variables as sets of influxdb compatible lines
general = assemblevar(model, connectionType, serial, firmware)
influxrow('general', general)

status = assemblevar(upTime,connectionStatus,connectionError)
influxrow('status', status)

wan = assemblevar(connectionTime, maxDownRate, maxUpRate, downRate, upRate, downPackageRate, upPackageRate, downTotal64, upTotal64)
influxrow('wan', wan)

if IS_DSL:
    dsl = assemblevar(dslDown, dslUp, dslMaxDown, dslMaxUp, noiseDown, noiseUp, powerDown, powerUp, attenuationDown, attenuationUp, hecError, hecErrorLocal, crcError, crcErrorLocal, fecError, fecErrorLocal )
    influxrow('dsl', dsl)

if IS_INTERNET_FACING:
    network = assemblevar(externalIP, dns, localDns, hostsEntry, hostsKnown, hostsKnownLAN, hostsKnownWLAN, hostsActive, hostsActiveLAN, hostsActiveWLAN)
else:
    network = assemblevar(localDns, hostsEntry, hostsKnown, hostsKnownLAN, hostsKnownWLAN, hostsActive, hostsActiveLAN, hostsActiveWLAN)
influxrow('network', network)

lan = assemblevar(lanPackageUp, lanPackageDown)
influxrow('lan', lan)

wlan24 = assemblevar(wlanName24, wlanChannel24, wlanClients24, wlanPackageUp24, wlanPackageDown24)
influxrow('wlan_2.4GHz', wlan24)

wlan50 = assemblevar(wlanName50, wlanChannel50, wlanClients50, wlanPackageUp50, wlanPackageDown50)
influxrow('wlan_5GHz', wlan50)

wlanGuest = assemblevar(wlanNameGuest, wlanChannelGuest, wlanClientsGuest, wlanPackageUpGuest, wlanPackageDownGuest)
influxrow('wlan_Guest', wlanGuest)
