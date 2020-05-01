FROM python:3.7.3

COPY . /app

WORKDIR /app

RUN pip3 install -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["./run_server.sh"]
