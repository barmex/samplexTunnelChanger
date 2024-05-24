FROM python:3.12-slim

COPY requirements.txt /
RUN pip3 install -r /requirements.txt
WORKDIR /app
COPY main.py /app
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8001"]