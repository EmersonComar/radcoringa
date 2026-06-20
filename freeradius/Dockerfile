FROM freeradius/freeradius-server:3.2.6

RUN apt-get update && \
    apt-get install -y freeradius-mysql mariadb-client gettext-base vim && \
    rm -rf /var/lib/apt/lists/*

COPY mods-enabled/sql /etc/freeradius/sql.template

COPY sites-enabled/default /etc/freeradius/sites-enabled/default
COPY mods-config/sql/main/mysql/queries.conf /etc/freeradius/mods-config/sql/main/mysql/queries.conf
COPY clients.conf /etc/freeradius/clients.conf

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN ln -s /etc/freeradius/mods-available/sqlippool /etc/freeradius/mods-enabled/sqlippool

RUN chown -R freerad:freerad /etc/freeradius/

USER freerad

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["freeradius", "-f", "-l", "stdout"]