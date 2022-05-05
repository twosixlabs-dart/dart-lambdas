FROM python:3.7.4-slim-buster

LABEL maintainer="john.hungerford@twosixlabs.com"

RUN pip3 install --upgrade pip

RUN pip3 install wheel twine

RUN pip3 install awscli --upgrade

RUN apt-get update -y

RUN apt-get -y install unzip

RUN apt-get -y install zip
