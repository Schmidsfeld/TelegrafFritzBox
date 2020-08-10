[![MIT license](https://img.shields.io/github/license/Schmidsfeld/TelefrafFritzBox?color=blue)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Schmidsfeld/TelefrafFritzBox/compare)
[![made-with-python](https://img.shields.io/badge/Python-3.7%2C%203.8-green)](https://www.python.org)
[![HitCount](http://hits.dwyl.com/Schmidsfeld/TelefrafFritzBox.svg)](http://hits.dwyl.com/Schmidsfeld/TelefrafFritzBox)

# TelegrafFritzBox
A Telegraf collector written in Phthon, gathering several crucial metrics for the Fritz!Box router by AVM via the TR-064 protocol. This collection includes a main phyton3 script, a telegraf config file and a Grafana dashboard.

The communication with the router is based on the FritzConnection library https://github.com/kbr/fritzconnection by Klaus Bremer.

For some future development of this script (especially with cable internet access) additional help is required. The script now has been sanatized not to crash if a varible is nout found. Please send me examples of your
'http://fritz.box:49000/tr64desc.xml'
If you have another connection type please check it there is an equivalent to the DSL statistics in there...

Forking and modifying this script is explicitly encouraged (hence you most likely need to adjust for your situation). I would appreciate if you drop me a note f you implement other stuff so I can backport it into the main script. 


## The End Result
Information that you get
* Full status of your current and past transfer speeds
* Current and possible line speeds
* The line dampening and noise margin
* The errors occurring the line
* Local networks (LAN and WLAN traffic)
* connected WLAN clients

![Grafana dashboard](doc/FritzBoxDashboard.png?raw=true)

## Details
### Concept
The script utilizes a single connection to the FritzBox router with the FritzConnection library. From there it reads out several service variable collections via TR-064. Note, that for performance reasons only one connection is established and every statistics output is only requested once. From the dictionary responses containing several variables each, the desired variables are extracted manually and parsed. The parsed arguments are then formatted appropriately as integers or strings according to the influxDB naming scheme. Lastly the gathered information is output as several lines in the format directly digested by Telegraf / InfluxDB.

### Output
* The output is formatted in the influxDB format. 
* By default the influxDB dataset FritzBox will be generated
* All datasets are tagged by the hostname of the router and grouped into different sources
* All names are sanitized (no "New" in variable names)
* All variables are cast into appropriate types (integer for numbers, string for expressions and float for 64bit total traffic)

![Grafana dashboard](doc/OutputScript.png?raw=true)

## Install
Several prerequisites need to be met to successfully install this script and generate the metrics. Some seem to be obvious but will be mentioned here for sake of complete documentation. 
* Have an operational TIG stack (Telegraf, InfluxDB Grafana) with all of them installed and operational.
* Activate the TR-064 protocoll in the Fritzbox (Heimnetz -> Netzwerk -> Netzwerkeinstellungen)
* Have a dedicated user on the Fritz!Box (the username:Telegraf is assumed, but any will do)
* Install python3 and pip  (for example: 'apt install python3-pip')
* Locally clone the fritzconnection library ('pip3 install fritzconnection')
* Clone this project ('git clone https://github.com/Schmidsfeld/TelegrafFritzBox/')
* Edit the python file and adjust the credentials '(nano ./TelegrafFritzBox/telegrafFritzBox.py')
* Make it executeamle ('chmod +x ./TelegrafFritzBox/telegrafFritzBox.py')
* Test the output ('python3 ./TelegrafFritzBox/telegrafFritzBox.py')
* Copy it to the appropiate locatio ('cp ./TelegrafFritzBox/telegrafFritzBox.py /usr/local/bin')
* Copy the Telegraf config file to the correct location or append it to your current file ('cp ./TelegrafFritzBox/telegrafFritzBox.conf /etc/telegraf/telegraf.d')
* Restart your Telegraf service ('systemctl restart telegraf')
* Load your Grafana dashboard (grafana/GrafanaFritzBoxDashboard.json)

## Future Plans
This Project is ready and tested locally, to ensure it is suiteable for publications, but not yet finished. For some parts I need help with additional testing (especially other connections than DSL). There are several things planned for future releases:
* Gather more stats (active clients in LAN, etc)
* Getting data about active phones and calls etc
* Read data from connected smarthome devices like the Fritz!DECT200
* Gather upstream information for cable based uplinks

## Docker and Telegraf

### Build the docker image yourself

```
docker build -t chevdor/fritzgraf . 
```

### Be lazy and use an existing image

```
docker pull chevdor/fritzgraf
```

### Start the container

First, you will need 2 files:
- one configuration file for telegraf
- one configuration file related to your router

Copy/edit:
- `.env-sample` into `.env`
- `telegrafDockerSample.conf` into `telegraf.conf``

Then run the container:

```
docker run --rm -it --env-file .env -v $PWD/telegraf.conf:/etc/telegraf/telegraf.conf:ro chevdor/fritzgraf
````

After 30s, you can connect to your influxdb and check.

```
influx --host IP_of_your_DockerImage
use telegraf
show series
````

