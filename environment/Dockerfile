FROM python:3.7.4

WORKDIR /code

COPY . .

RUN pip install -r requests.txt

EXPOSE 8080
CMD [ "python", "environment.py" ]