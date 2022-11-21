FROM python:3.11-slim-buster

RUN mkdir /src
WORKDIR /src/
COPY requirements.txt requirements.txt
COPY . .

RUN pip3 install -U pip wheel
RUN pip3 install -r requirements.txt
RUN pip3 install -e .

CMD ["barcodecop", "-h"]
