# DEV DOCKER FILE - RUNS DJANGO DEV SERVER
# build img with: "docker build -t drodos ."
# run img with: "docker run -p 8000:80 drodos"
FROM python:3
ENV PYTHONUNBUFFERED=1
EXPOSE 80
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
CMD ["python", "manage.py", "runserver", "0.0.0.0:80"]