FROM bcgovimages/von-image:py36-1.11-1

ENV ENABLE_PTVSD 0

ADD requirements*.txt ./

RUN pip3 install --no-cache-dir -r requirements.txt -r requirements.dev.txt

COPY aries_cloudagent ./aries_cloudagent
COPY aries-acapy-plugin-toolbox ./aries-acapy-plugin-toolbox
COPY bin ./bin
COPY README.md ./
COPY setup.py ./
COPY startup.sh ./

RUN pip3 install --no-cache-dir -e ".[indy]"
RUN /bin/bash -c "python3 -m venv env"
RUN /bin/bash -c "source env/bin/activate"
RUN /bin/bash -c "pip3 install -e /home/indy/aries-acapy-plugin-toolbox"

USER root
