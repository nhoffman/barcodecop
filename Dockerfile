FROM python:3.11-slim-buster

WORKDIR /src/
COPY . .

RUN pip3 install -U pip wheel
RUN python3 setup.py install
CMD ["barcodecop", "-h"]
