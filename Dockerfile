FROM python:3.8
USER root
WORKDIR /app

ADD ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt 

ADD . /app
RUN pip install -r requirements.txt

EXPOSE 80

ENV NAME World

CMD ["python", "index.py"]