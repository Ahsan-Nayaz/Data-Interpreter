# Base image
FROM ubuntu:18.04

# fix locales
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales \
    && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

ENV LANG en_US.utf8
# Set environment variables to disable prompts
ENV DEBIAN_FRONTEND=noninteractive

# Create user with sudo only in the container for security.
RUN useradd docker && echo "docker:docker" | chpasswd && mkdir -p /home/docker && chown docker:docker /home/docker
RUN mkdir -p /mnt/data && chown -R docker:docker /mnt/data

RUN apt-get update && apt-get install -y sudo

RUN usermod -aG sudo docker

RUN echo "docker ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
# add write perms for user 'docker' in the correct dirs ( where it cant mess things up much. it does have passwordless sudo, so it can override this if it figures out it has sudo.)
RUN chown -R docker:docker /mnt/data

# install blobfuse
#RUN #sudo dpkg --add-architecture amd64
#RUN sudo apt-get update \
#    && sudo apt-get install -y wget apt-utils \
#    && sudo wget packages.microsoft.com/ubuntu/18.04/prod/pool/main/b/blobfuse/blobfuse-1.1.1-bionic.deb   \
#    && sudo dpkg -i blobfuse-1.1.1-bionic.deb  \
#    && sudo apt-get remove -y wget \
#    && sudo apt-get update \
#    && sudo apt-get install -y --no-install-recommends libcurl3-gnutls libgnutls30 \
#    && sudo rm -rf /var/lib/apt/lists/*
#RUN sudo apt-get update
##RUN sudo apt-get install blobfuse fuse -y
#RUN sudo mkdir /mnt/blobfusetmp
#RUN sudo chown docker /mnt/blobfusetmp
#RUN sudo mount -t tmpfs -o size=16g tmpfs /mnt/blobfusetmp
#COPY connection.cfg /config/
#RUN sudo mkdir /data/
#RUN sudo blobfuse /data/ --tmp-path=/mnt/blobfusetmp  --config-file=/config/connection.cfg -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120 -o allow_other

RUN sudo apt-get install aptitude -y
# Update package list and install essential utilities and runtimes
RUN sudo apt-get update && aptitude install -y \
    jq \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    libssl-dev \
    libexpat1 \
    r-base \
    r-base-dev

# install nodejs stuff
RUN sudo apt-get update
RUN sudo apt-get install -y ca-certificates curl gnupg
RUN sudo mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN NODE_MAJOR=20
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
RUN sudo apt-get update
RUN sudo aptitude install nodejs -y
RUN pip3 install "Cython<=3.0"
#RUN pip3 install numpy
#RUN pip3 install pandas
#RUN pip3 install matplotlib
# Copy unified requirements.txt into the image
COPY ./requirements.txt /tmp/

# Install Python packages
#RUN awk '/\[python\]/, /^\s*$/' /tmp/requirements.txt | grep -v '^\[python\]' > /tmp/python_requirements.txt && \
#    pip3 install --no-cache-dir -r /tmp/python_requirements.txt --no-input

# Create an initial empty package.json
RUN echo '{}' > /tmp/package.json

#RUN awk '/\[node\]/, /^\s*$/' /tmp/requirements.txt | grep -v '^\[node\]' > /tmp/node_requirements.txt && \
#    while read -r package; do \
#        name=$(echo $package | grep -Eo "^[a-zA-Z0-9_-]+") && \
#        version=$(echo $package | grep -Eo "[>=<]+[0-9.]+"); \
#        if [ -z "$version" ]; then version="*"; fi && \
#        jq ".dependencies.\"$name\" = \"$version\"" /tmp/package.json > /tmp/package_temp.json && mv /tmp/package_temp.json /tmp/package.json; \
#    done < /tmp/node_requirements.txt


#RUN sudo aptitude install npm -y
## Install NodeJS packages
#RUN npm install --save --yes --no-package-lock --prefix /tmp

## Install R packages
#RUN awk '/\[r\]/,/^\s*$/' /tmp/requirements.txt | grep -v '^\[r\]' > /tmp/r_requirements.txt && \
#    while read -r package; do \
#        R -e "install.packages('$package', repos='http://cran.rstudio.com/', dependencies=TRUE, INSTALL_opts = c('--no-tests'))"; \
#    done < /tmp/r_requirements.txt

# Install NodeJS packages

# Remove temporary files
#RUN rm /tmp/package.json /tmp/node_requirements.txt /tmp/python_requirements.txt /tmp/r_requirements.txt

#Blobfuse
#RUN sudo apt-get install git -y
#RUN git clone https://github.com/Azure/azure-storage-fuse/
RUN sudo apt-get install pkg-config libfuse-dev cmake libcurl4-gnutls-dev libgnutls28-dev uuid-dev libgcrypt20-dev libboost-all-dev gcc g++ -y
##RUN cd azure-storage-fuse
#RUN chmod 755 azure-storage-fuse/build.sh
#RUN sh azure-storage-fuse/build.sh
RUN apt-get update \
    && apt-get install -y wget apt-utils \
    && wget https://packages.microsoft.com/config/ubuntu/18.04/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb
RUN sudo apt-get update
RUN sudo apt-get install blobfuse fuse -y
RUN sudo mkdir /blobfusetmp/
RUN sudo chown docker /blobfusetmp/
#RUN sudo mount -t tmpfs -o size=16g tmpfs /blobfusetmp/
COPY connection.cfg /config/
RUN sudo mkdir /data/
RUN sudo blobfuse /data/ --tmp-path=/blobfusetmp/  --use-https=true --config-file=/config/connection.cfg -o attr_timeout=240 -o entry_timeout=240 -o negative_timeout=120 -o allow_other

# workdir set. pray it dosent try to go exploring.
WORKDIR /mnt/data
