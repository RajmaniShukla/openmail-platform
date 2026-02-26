# OpenMail - Postfix SMTP Server
FROM debian:bookworm-slim

# Install packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    postfix \
    postfix-pgsql \
    libsasl2-modules \
    sasl2-bin \
    opendkim \
    opendkim-tools \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create mail directories
RUN mkdir -p /var/mail/vhosts && \
    groupadd -g 5000 vmail && \
    useradd -g vmail -u 5000 vmail -d /var/mail && \
    chown -R vmail:vmail /var/mail

# Copy configuration files
COPY main.cf /etc/postfix/main.cf
COPY master.cf /etc/postfix/master.cf
COPY pgsql-*.cf /etc/postfix/
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Expose ports
EXPOSE 25 587 465

# Volume for mail storage
VOLUME ["/var/mail/vhosts", "/etc/ssl/mail"]

ENTRYPOINT ["/entrypoint.sh"]
CMD ["postfix", "start-fg"]
