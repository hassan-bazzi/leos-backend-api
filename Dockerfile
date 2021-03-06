FROM python:3.7.3

RUN apt update
RUN apt install vim less -y

COPY . /app

WORKDIR /app

RUN pip3 install -r requirements.txt

RUN mkdir -p /log;

EXPOSE 8000

ENTRYPOINT ["./run_server.sh"]
