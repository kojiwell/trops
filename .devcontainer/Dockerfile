FROM ubuntu:22.04

ARG USER=devuser
ARG UID=1000
ARG GID=1000
RUN useradd -m ${USER} --uid=${UID} --shell /usr/bin/bash

# Install dependent packages
RUN apt update \
 && apt install -y git python3 python3-pip python3-venv curl wget vim sudo
RUN echo "devuser ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/devuser

USER ${UID}:${GID}
# Install poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
