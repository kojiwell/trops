FROM ubuntu:22.04

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && \
    apt install -y python3 python3-pip git vim sudo ansible zsh

ADD root/.bashrc /root/.bashrc
ADD root/.zshrc /root/.zshrc

WORKDIR /root
