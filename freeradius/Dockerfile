FROM freeradius/freeradius-server:3.2.6

RUN apt-get update && \
    apt-get install -y freeradius-mysql mariadb-client vim && \
    rm -rf /var/lib/apt/lists/*

COPY mods-enabled/sql /etc/freeradius/mods-enabled/sql
COPY sites-enabled/default /etc/freeradius/sites-enabled/default
COPY mods-config/sql/main/mysql/queries.conf /etc/freeradius/mods-config/sql/main/mysql/queries.conf
COPY clients.conf /etc/freeradius/clients.conf

RUN chown -R freerad:freerad /etc/freeradius/

USER freerad

CMD ["freeradius", "-x"]