#!/bin/bash
set -e

# Substitute environment variables in config files
if [ -n "$MAIL_HOSTNAME" ]; then
    sed -i "s/myhostname = .*/myhostname = $MAIL_HOSTNAME/" /etc/postfix/main.cf
fi

if [ -n "$MAIL_DOMAIN" ]; then
    sed -i "s/mydomain = .*/mydomain = $MAIL_DOMAIN/" /etc/postfix/main.cf
fi

if [ -n "$POSTGRES_HOST" ]; then
    sed -i "s/hosts = .*/hosts = $POSTGRES_HOST/" /etc/postfix/pgsql-*.cf
fi

if [ -n "$POSTGRES_USER" ]; then
    sed -i "s/user = .*/user = $POSTGRES_USER/" /etc/postfix/pgsql-*.cf
fi

if [ -n "$POSTGRES_PASSWORD" ]; then
    sed -i "s/password = .*/password = $POSTGRES_PASSWORD/" /etc/postfix/pgsql-*.cf
fi

if [ -n "$POSTGRES_DB" ]; then
    sed -i "s/dbname = .*/dbname = $POSTGRES_DB/" /etc/postfix/pgsql-*.cf
fi

# Set permissions
chown -R vmail:vmail /var/mail/vhosts
chmod -R 770 /var/mail/vhosts

# Generate aliases database
newaliases 2>/dev/null || true

# Fix permissions on config files
chmod 640 /etc/postfix/pgsql-*.cf
chown root:postfix /etc/postfix/pgsql-*.cf

echo "Starting Postfix..."
exec "$@"
