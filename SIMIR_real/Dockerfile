FROM zeek/zeek:latest

# Instala dependências essenciais, incluindo Python e utilitários para SIMIR
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ cmake make libpcap-dev iproute2 net-tools gdb nano curl gettext \
    python3 python3-pip nmap \
    iputils-ping nginx php-fpm php-cli \
    && rm -rf /var/lib/apt/lists/*
    
    
COPY site/ /usr/local/zeek/share/zeek/site/

# Copia scripts SIMIR essenciais (necessários para funcionamento do container)
COPY scripts/essential/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY scripts/essential/check-interface.sh /usr/local/bin/check-interface.sh
COPY scripts/essential/setup-permissions.sh /usr/local/bin/setup-permissions.sh
COPY scripts/essential/simir-monitor.py /usr/local/bin/simir-monitor.py
COPY scripts/essential/simir-autostart.sh /usr/local/bin/simir-autostart.sh

# Define permissões para todos os scripts
RUN chmod +x /usr/local/bin/entrypoint.sh \
    /usr/local/bin/check-interface.sh \
    /usr/local/bin/setup-permissions.sh \
    /usr/local/bin/simir-monitor.py \
    /usr/local/bin/simir-autostart.sh

# Cria diretórios para SIMIR
RUN mkdir -p /opt/simir/scripts /opt/simir/config /var/log/simir

 WORKDIR /usr/local/zeek
# Expõe portas comuns
EXPOSE 47760 47761

COPY alert_data.php /usr/local/www/zeek-api/
RUN chmod 644 /usr/local/www/zeek-api/alert_data.php
RUN chown www-data:www-data /usr/local/www/zeek-api/alert_data.php
RUN mkdir -p /var/run/php
RUN sed -i 's/;listen.mode = .*/listen.mode = 0660/' /etc/php/*/fpm/pool.d/www.conf
RUN sed -i 's/;listen.owner = .*/listen.owner = www-data/' /etc/php/*/fpm/pool.d/www.conf
RUN sed -i 's/;listen.group = .*/listen.group = www-data/' /etc/php/*/fpm/pool.d/www.conf
RUN sed -i 's/listen = .*/listen = \/var\/run\/php\/php-fpm.sock/' /etc/php/*/fpm/pool.d/www.conf

# Ensure nginx user can access the socket
RUN usermod -a -G www-data nginx || true
# FIXED nginx configuration - bind to all interfaces
RUN echo 'server {\n\
    listen 8090 default_server;\n\
    listen [::]:8090 default_server;\n\
	root /usr/local/www;\n\
	index index.php index.html;\n\
	\n\
	location / {\n\
	    try_files $uri $uri/ =404;\n\
	}\n\
	\n\
	location ~ \.php$ {\n\
	    include fastcgi_params;\n\
	    fastcgi_pass unix:/var/run/php/php-fpm.sock;\n\
	    fastcgi_param SCRIPT_FILENAME $request_filename;\n\
	}\n\
}' > /etc/nginx/sites-available/default

# Fix PHP configuration to listen on socket with proper permissions
 

# Create necessary directories and fix permissions
RUN mkdir -p /var/lib/nginx /var/log/nginx \
    && chown -R www-data:www-data /usr/local/www/ \
    && chmod 755 /usr/local/www/zeek-api/alert_data.php
    
    
# Define o entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
