FROM ubuntu:22.04

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && \
    apt install -y python3 python3-pip git vim sudo ansible zsh curl

RUN curl -sL https://j.mp/glab-cli | sh

RUN useradd -m -s /usr/bin/bash user1
ADD home/user1/.bashrc /home/user1/.bashrc
RUN chown user1:user1 /home/user1/.bashrc

ADD root/.bashrc /root/.bashrc
ADD root/.zshrc /root/.zshrc
ADD etc/sudoers.d/user1 /etc/sudoers.d/user1

WORKDIR /root
