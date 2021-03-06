#!/bin/bash

MSB_PROTO=`echo $MSB_PROTO`
MSB_IP=`echo $MSB_ADDR | cut -d: -f 1`
MSB_PORT=`echo $MSB_ADDR | cut -d: -f 2`

if [ $MSB_IP ]; then
    sed -i "s|MSB_SERVICE_IP = .*|MSB_SERVICE_IP = '$MSB_IP'|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
fi

if [ $MSB_PROTO ]; then
    sed -i "s|MSB_SERVICE_PROTOCOL = .*|MSB_SERVICE_PROTOCOL = '$MSB_PROTO'|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
fi

if [ $MSB_PORT ]; then
    sed -i "s|MSB_SERVICE_PORT = .*|MSB_SERVICE_PORT = '$MSB_PORT'|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
fi

if [ $SERVICE_IP ]; then
    sed -i "s|\"ip\": \".*\"|\"ip\": \"$SERVICE_IP\"|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
fi

if [ $REG_TO_MSB_WHEN_START ]; then
    sed -i "s|REG_TO_MSB_WHEN_START = .*|REG_TO_MSB_WHEN_START = '$REG_TO_MSB_WHEN_START'|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
fi

if [ $SSL_ENABLED ]; then
    sed -i "s|SSL_ENABLED = .*|SSL_ENABLED = '$SSL_ENABLED'|"  vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
fi

sed -i "s/127.0.0.1:80/$MSB_IP:$MSB_PORT/" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py

# Configure MYSQL
MYSQL_IP=`echo $MYSQL_ADDR | cut -d: -f 1`
MYSQL_PORT=`echo $MYSQL_ADDR | cut -d: -f 2`
echo "MYSQL_ADDR=$MYSQL_ADDR"

if [ $REDIS_ADDR ]; then
    REDIS_IP=`echo $REDIS_ADDR | cut -d: -f 1`
else
    REDIS_IP="$MYSQL_ADDR"
fi

sed -i "s|DB_IP.*|DB_IP = '$MYSQL_IP'|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
sed -i "s|DB_PORT.*|DB_PORT = $MYSQL_PORT|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
sed -i "s|REDIS_HOST.*|REDIS_HOST = '$REDIS_IP'|" vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py

cat vfc/gvnfm/vnflcm/lcm/lcm/pub/config/config.py
