FROM python:3.11

WORKDIR /app

RUN python -m pip install --upgrade pip
RUN pip install gunicorn playwright
RUN python -m playwright install --with-deps chromium

COPY requirements.txt .
RUN pip install -r requirements.txt

CMD python -m rielgobot_pro
