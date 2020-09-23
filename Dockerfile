FROM python:3.7

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . ./

CMD cp -n  ./*.json /data || true && python main.py