#!/bin/bash
set -e

# Substitute environment variables in config files
if [ -n "$POSTGRES_HOST" ]; then
    sed -i "s/host=postgres/host=$POSTGRES_HOST/" /etc/dovecot/dovecot-sql.conf.ext
fi

if [ -n "$POSTGRES_USER" ]; then
    sed -i "s/user=openmail/user=$POSTGRES_USER/" /etc/dovecot/dovecot-sql.conf.ext
fi

if [ -n "$POSTGRES_PASSWORD" ]; then
    sed -i "s/password=openmail/password=$POSTGRES_PASSWORD/" /etc/dovecot/dovecot-sql.conf.ext
fi

if [ -n "$POSTGRES_DB" ]; then
    sed -i "s/dbname=openmail/dbname=$POSTGRES_DB/" /etc/dovecot/dovecot-sql.conf.ext
fi

# Set permissions
chown -R vmail:vmail /var/mail/vhosts
chmod -R 770 /var/mail/vhosts

# Create default sieve directory
mkdir -p /var/mail/vhosts/global-sieve
chown -R vmail:vmail /var/mail/vhosts/global-sieve

echo "Starting Dovecot..."
exec "$@"
