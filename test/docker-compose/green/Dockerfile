FROM ubuntu:20.04

RUN apt update && \
    apt install -y python3 python3-pip git vim sudo

ADD root/.bashrc /root/.bashrc

#RUN useradd -m ktanaka -s /usr/bin/bash
#ADD home/ktanaka/.bashrc /home/ktanaka/.bashrc
#RUN chown ktanaka:ktanaka /home/ktanaka/.bashrc

WORKDIR /root
