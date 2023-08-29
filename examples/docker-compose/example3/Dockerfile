FROM ubuntu:22.04

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && \
    apt install -y python3 python3-pip git vim sudo ansible zsh curl

RUN curl -sL https://j.mp/glab-cli | sh

ADD root/.bashrc /root/.bashrc
ADD root/.zshrc /root/.zshrc
ADD root/.ssh /root/.ssh
RUN chown -R root:root /root && \
    chmod 700 /root/.ssh

WORKDIR /root
