FROM python:3.7.4

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requests.txt

EXPOSE 8080
CMD [ "python", "agent.py" ]