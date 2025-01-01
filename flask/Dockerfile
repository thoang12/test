FROM thobaby/flask4:0.1
WORKDIR /app
RUN apt update && apt install -y python3-pip mysql-client-core-8.0
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "5", "--bind", "0.0.0.0:5000", "app:app"]
