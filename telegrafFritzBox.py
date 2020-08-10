#!/opt/bin/python3

from fritzconnection import FritzConnection
import sys
import os

FRITZBOX_IP = os.environ.get('FRITZ_IP', '192.168.178.1')
FRITZBOX_USER = os.environ.get('FRITZ_USER', 'telegraf')
FRITZBOX_PASSWORD = os.environ.get('Fritz_PASSWD', "SuperStrongPassword")
FRITZBOX_ID = os.environ.get('FRITZ_ID', 'FritzBox')

#For sesting purpose
FRITZBOX_CONNECTION_DSL = True #set to false if you have a cable or IP upstream

try:
    fc = FritzConnection(address=FRITZBOX_IP, user=FRITZBOX_USER, password=FRITZBOX_PASSWORD, timeout=2.0)
except BaseException:
    print("Cannot connect to fritzbox.")
    sys.exit(1)

def readfritz(module, action):
    try:
        answer = fc.call_action(module, action)
    except:
        answer = dict() #return an emty dict in case of failure
    return answer

def extractvar(answer, variable, integer=False, string=False, name=""):
    if variable in answer.keys():
        avar = str(answer[variable])
        if name == "":
            name = variable
        if integer:
            avar = name + '=' + avar +'i' #format for integers in influxDB
        else:
            if string:
                avar = name + '="' + avar +'"' #format for strings in influxDB
            else:
                avar = name + '=' + avar #format for float/double in influxDB
    else:
        avar = ''
    return avar

def assemblevar(*args):
    data = ','.join(list(args))+','
    #cleaning up output
    data = data.replace("New", "")
    data = data.replace(",,",",") 
    data = data.replace(",,",",")
    data = data[:-1]
    return data

def influxrow(tag, data):
    influx = FRITZBOX_ID +','+ fbName +  ',source=' + tag + ' ' + data 
    print(influx)

#Get FritzBox variables
deviceInfo = readfritz('DeviceInfo1', 'GetInfo')
wanInfo = readfritz('WANCommonIFC1', 'GetCommonLinkProperties')
trafficInfo = readfritz('WANCommonIFC1', 'GetAddonInfos')
#connectionInfo = readfritz('WANIPConn1', 'GetStatusInfo') 
connectionInfo = readfritz('WANPPPConnection1', 'GetInfo') 
dslInfo = readfritz('WANDSLInterfaceConfig1', 'GetInfo')
dslError = readfritz('WANDSLInterfaceConfig1', 'GetStatisticsTotal')
dslInfo = readfritz('WANDSLInterfaceConfig1', 'GetInfo')
fritzInfo = readfritz('LANHostConfigManagement1', 'GetInfo')
dhcpInfo = readfritz('Hosts1', 'GetHostNumberOfEntries')
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

#Parse single variables into influxdb compatible strings
#General settings of the FritzBox
firmware = 'Firmware="'+ fc.device_manager.system_version+'"' 
model = extractvar(deviceInfo, 'NewModelName', False)
serial = extractvar(deviceInfo, 'NewSerialNumber', False)
fbName = extractvar(fritzInfo, 'NewDomainName', False,'host')
upTime = extractvar(deviceInfo, 'NewUpTime', True)
connectionType = extractvar(wanInfo, 'NewWANAccessType', False, True)

#FritzBox traffic and line speed information
maxDownRate = extractvar(wanInfo, 'NewLayer1DownstreamMaxBitRate', True)
maxUpRate = extractvar(wanInfo, 'NewLayer1UpstreamMaxBitRate', True)
downRate = extractvar(trafficInfo, 'NewByteReceiveRate', True)
upRate = extractvar(trafficInfo, 'NewByteSendRate', True)
downPackageRate = extractvar(trafficInfo, 'NewPacketReceiveRate', True)
upPackageRate = extractvar(trafficInfo, 'NewPacketSendRate', True)
downTotal = extractvar(trafficInfo, 'NewTotalBytesReceived', True)
upTotal = extractvar(trafficInfo, 'NewTotalBytesSent', True)
downTotal64 = extractvar(trafficInfo, 'NewX_AVM_DE_TotalBytesReceived64', False, False, 'TotalBytesReceived64' )
upTotal64 = extractvar(trafficInfo, 'NewX_AVM_DE_TotalBytesSent64', False, False,'TotalBytesSent64')

# Stats seemingly only available on DSL
connectionTime = extractvar(connectionInfo, 'NewUptime', True, 'ConnectionTime')
connectionStatus = extractvar(connectionInfo, 'NewConnectionStatus', False, True)
connectionError = extractvar(connectionInfo, 'NewLastConnectionError', False, True, 'LastError')
externalIP = extractvar(connectionInfo, 'NewExternalIPAddress', False, True)
dns = extractvar(connectionInfo, 'NewDNSServers', False, True)

# Try to extract all the DSL Statistics
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

#LocalNetwork Information
localDns = extractvar(fritzInfo, 'NewDNSServers', False, True,'LocalDNSServer')
hostsKnown = extractvar(dhcpInfo, 'NewHostNumberOfEntries', True, False)

# Local network stransfers. Bytes are not available on WLAN so packages are used as a metric 
lanPackageUp = extractvar(lanStat, 'NewPacketsSent', True)
lanPackageDown = extractvar(lanStat, 'NewPacketsReceived', True)
wlanPackageUp24 = extractvar(wlanStat24, 'NewTotalPacketsSent', True, False, 'PacketsSent' )
wlanPackageDown24 = extractvar(wlanStat24, 'NewTotalPacketsReceived', True,  False, 'PacketsReceived')
wlanPackageUp50 = extractvar(wlanStat50, 'NewTotalPacketsSent', True, False, 'PacketsSent')
wlanPackageDown50 = extractvar(wlanStat50, 'NewTotalPacketsReceived', True, False, 'PacketsReceived')
wlanPackageUpGuest = extractvar(wlanStatGuest, 'NewTotalPacketsSent', True, False, 'PacketsSent')
wlanPackageDownGuest = extractvar(wlanStatGuest, 'NewTotalPacketsReceived',True, False, 'PacketsReceived')
wlanName24 = extractvar(wlanInfo24, 'NewSSID', False, True)
wlanName50 = extractvar(wlanInfo50, 'NewSSID', False, True) 
wlanNameGuest = extractvar(wlanInfoGuest, 'NewSSID', False, True) 
wlanChannel24 = extractvar(wlanInfo24, 'NewChannel', True)
wlanChannel50 = extractvar(wlanInfo50, 'NewChannel', True)
wlanChannelGuest = extractvar(wlanInfoGuest, 'NewChannel', True)
wlanClients24 = extractvar(wlanAssoc24, 'NewTotalAssociations', True, False, 'ClientsNumber')
wlanClients50 = extractvar(wlanAssoc50, 'NewTotalAssociations', True, False, 'ClientsNumber')
wlanClientsGuest = extractvar(wlanAssocGuest, 'NewTotalAssociations', True, False, 'ClientsNumber')


#Output variables as sets of influxdb compatible lines 
general = assemblevar(model, connectionType, serial, firmware)
influxrow('general', general)

status = assemblevar(upTime,connectionStatus,connectionError)
influxrow('status', status)

wan = assemblevar(connectionTime, maxDownRate, maxUpRate, downRate, upRate,  downPackageRate, upPackageRate, downTotal, upTotal, downTotal64, upTotal64)
influxrow('wan', wan)

if FRITZBOX_CONNECTION_DSL:
    dsl = assemblevar(dslDown, dslUp, dslMaxDown, dslMaxUp, noiseDown, noiseUp, powerDown, powerUp, attenuationDown, attenuationUp, hecError, hecErrorLocal, crcError, crcErrorLocal, fecError, fecErrorLocal )
    influxrow('dsl', dsl)

network = assemblevar(externalIP, dns, localDns, hostsKnown)
influxrow('network', network)

lan = assemblevar(lanPackageUp, lanPackageDown)
influxrow('lan', lan)

wlan24 = assemblevar(wlanName24, wlanChannel24, wlanClients24, wlanPackageUp24, wlanPackageDown24)
influxrow('wlan_2.4GHz', wlan24)

wlan50 = assemblevar(wlanName50, wlanChannel50, wlanClients50, wlanPackageUp50, wlanPackageDown50)
influxrow('wlan_5GHz', wlan50)

wlanGuest = assemblevar(wlanNameGuest, wlanChannelGuest, wlanClientsGuest, wlanPackageUpGuest, wlanPackageDownGuest)
influxrow('wlan_Guest', wlanGuest)
