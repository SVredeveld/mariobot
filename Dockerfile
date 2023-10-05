FROM python:3.9-slim

WORKDIR /usr/src/app

COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# NOTE: You'll have to set these values when running the container
ENV SLACK_TOKEN=""
ENV AZURE_CONNECTIONSTRING=""

CMD ["python", "./app.py"]
