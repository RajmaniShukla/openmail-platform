# OpenMail - Dovecot IMAP/POP3 Server
FROM debian:bookworm-slim

# Install packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    dovecot-core \
    dovecot-imapd \
    dovecot-pop3d \
    dovecot-lmtpd \
    dovecot-pgsql \
    dovecot-sieve \
    dovecot-managesieved \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create mail directories
RUN mkdir -p /var/mail/vhosts && \
    groupadd -g 5000 vmail && \
    useradd -g vmail -u 5000 vmail -d /var/mail && \
    chown -R vmail:vmail /var/mail

# Copy configuration files
COPY dovecot.conf /etc/dovecot/dovecot.conf
COPY conf.d/ /etc/dovecot/conf.d/
COPY dovecot-sql.conf.ext /etc/dovecot/dovecot-sql.conf.ext
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && \
    chmod 600 /etc/dovecot/dovecot-sql.conf.ext

# Expose ports
EXPOSE 143 993 110 995 24

# Volume for mail storage
VOLUME ["/var/mail/vhosts", "/etc/ssl/mail"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["dovecot", "-F"]
