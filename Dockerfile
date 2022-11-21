FROM python:3.11-slim-buster

RUN mkdir /src
WORKDIR /src/
COPY . .

RUN pip3 install -U pip wheel
RUN python3 setup.py install
CMD ["barcodecop", "-h"]
