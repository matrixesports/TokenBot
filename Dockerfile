FROM python:3.7

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . ./

CMD python main.py to CMD cp -n ./*.db ./*.json /data || true && python main.py