# Use an official Python image as the base
FROM python:3.11-slim

# Set environment variables to prevent Python from generating .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
# (Note: in Docker Compose development mode, this will be volume-mounted)
COPY . /app

# Expose the port FastAPI will run on
EXPOSE 8090

# Command to run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8090", "--reload"]
