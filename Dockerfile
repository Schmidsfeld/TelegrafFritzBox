FROM telegraf
LABEL maintainer "chevdor@gmail.com"
LABEL description="Based on telegraf, this image adds python3 and a telegraf input script to feed fritbox metrics into an influxdb"

WORKDIR /usr/local/bin
RUN apt-get update && \
	apt-get upgrade -y && \
	apt-get install -y python3 python3-pip && \
    pip3 install fritzconnection
    
# VOLUME /etc/telegraf/telegraf.conf

ENV TGFB_IP=192.168.178.1
ENV TGFB_USER=telegraf
ENV TGFB_PASSWD=
ENV TGFB_ID=FritzBox

COPY telegrafFritzBox.py /usr/local/bin
