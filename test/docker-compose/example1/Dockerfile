FROM ubuntu:22.04

ENV TZ=Asia/Tokyo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update && \
    apt install -y python3 python3-pip git vim sudo ansible zsh curl

RUN curl -sL https://j.mp/glab-cli | sh

RUN useradd -m -s /usr/bin/bash user1
ADD home/user1/.bashrc /home/user1/.bashrc
ADD home/user1/.ssh /home/user1/.ssh
RUN chown -R user1:user1 /home/user1 && \
    chmod 700 /home/user1/.ssh

ADD root/.bashrc /root/.bashrc
ADD root/.zshrc /root/.zshrc
ADD etc/sudoers.d/user1 /etc/sudoers.d/user1
ADD root/.ssh /root/.ssh
RUN chown -R root:root /root && \
    chmod 700 /root/.ssh

USER user1
WORKDIR /home/user1