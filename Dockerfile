FROM bcgovimages/von-image:py36-1.11-1

ENV ENABLE_PTVSD 0

ADD requirements*.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt -r requirements.dev.txt

COPY . .
RUN pip3 install --no-cache-dir -e ".[indy]"
# ADD env ./env
RUN /bin/bash -c "source env/bin/activate"
RUN pip3 install git+https://github.com/hyperledger/aries-acapy-plugin-toolbox.git@master#egg=acapy-plugin-toolbox

USER root
