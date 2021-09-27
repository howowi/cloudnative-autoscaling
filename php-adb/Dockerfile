FROM docker.io/php:7.4-fpm
ADD index.php /var/www/html/
ADD process.php /var/www/html/
RUN chmod 444 /var/www/html/index.php && chmod 444 /var/www/html/process.php
RUN mkdir /opt/oracle
RUN cd /opt/oracle && curl https://download.oracle.com/otn_software/linux/instantclient/1912000/oracle-instantclient19.12-basic-19.12.0.0.0-1.x86_64.rpm -o instantclient_basic_19_12.rpm
RUN cd /opt/oracle && curl https://download.oracle.com/otn_software/linux/instantclient/1912000/oracle-instantclient19.12-devel-19.12.0.0.0-1.x86_64.rpm -o instantclient_sdk_19_12.rpm
RUN apt-get update && apt-get install alien libaio1 unzip -y
RUN alien -i /opt/oracle/instantclient_basic_19_12.rpm && alien -i /opt/oracle/instantclient_sdk_19_12.rpm
RUN pecl install oci8-2.2.0 && docker-php-ext-enable oci8.so
COPY php.ini $PHP_INI_DIR/php.ini
RUN rm -rf /opt/oracle/*
ADD Wallet_PHPADB.zip /opt/oracle/Wallet_PHPADB.zip
RUN cd /opt/oracle && unzip /opt/oracle/Wallet_PHPADB.zip
COPY sqlnet.ora /opt/oracle/sqlnet.ora
RUN chmod 644 /opt/oracle/sqlnet.ora