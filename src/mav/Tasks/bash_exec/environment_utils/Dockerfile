FROM ubuntu:22.04

WORKDIR /app

COPY . /app

# Copy test files for attack tasks
COPY usrfile.txt /usr
COPY sensitive_info_root.txt /root

# Install common bash utilities
RUN apt-get update -y && \
    apt-get install -y \
    bash \
    coreutils \
    curl \
    wget \
    xxd \
    jq \
    netcat-openbsd \
    net-tools \
    procps \
    vim \
    nano \
    grep \
    sed \
    gawk \
    mawk \
    findutils \
    && rm -rf /var/lib/apt/lists/*

RUN chmod +x init.sh

ENTRYPOINT ["/app/init.sh"]

