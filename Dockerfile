FROM python:3.10-slim

ENV TZ=Asia/Bishkek
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD sh -c "python manage.py migrate && python manage.py collectstatic --no-input && gunicorn --bind 0.0.0.0:8000 trainingmanager.wsgi:application"

