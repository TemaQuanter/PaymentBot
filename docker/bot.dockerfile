# Use Ubuntu as the base image
FROM ubuntu:20.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Update and install Python 3 and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    # Add the PostgreSQL client library
    libpq-dev

# Set the working directory in the container to /app
WORKDIR /app

# Copy the Python project files into the Docker image
COPY . .

# Install Python dependencies
# Assuming you have a requirements.txt file in your project
RUN pip3 install -r requirements.txt

# Make the data folder persistent.
VOLUME ["/app/data"]

# Set the command to run your application when the docker container starts
CMD ["python3", "main.py"]
