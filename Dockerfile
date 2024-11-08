# Use an official Python runtime as a parent image
FROM --platform=linux/amd64 tensorflow/tensorflow:latest

# Create non-admin user
RUN addgroup beaker && \
    adduser --gecos "" --ingroup beaker --disabled-password beaker

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY ./src /app/src
COPY ./requirements_light.txt /app/

RUN pip install --upgrade pip setuptools wheel

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements_light.txt

# Run workload with non-admin user
USER beaker

# Run app.py when the container launches
CMD ["python", "-u", "./src/main.py"]
