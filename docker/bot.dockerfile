# Use an official Python runtime as a parent image
FROM python:3.12

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Update and install the PostgreSQL client library
RUN apt-get update && apt-get install -y libpq-dev

# Set the working directory in the container to /app
WORKDIR /app

# Copy the Python project files into the Docker image
COPY . .

# Install Python dependencies
# Assuming you have a requirements.txt file in your project
RUN pip install -r requirements.txt

# Make the data folder persistent.
VOLUME ["/app/data"]

# Set the command to run your application when the docker container starts
CMD ["python", "main.py"]
