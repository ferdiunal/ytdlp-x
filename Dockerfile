# Use an official Python runtime as the base image
FROM --platform=$BUILDPLATFORM python:3.9-alpine

RUN apk add --no-cache ffmpeg

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Create a directory for cookies
RUN mkdir -p /app/cookies && mkdir -p /app/output

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--timeout", "300", "app:app"]