# Use a specific, stable version of Python as the base
FROM python

# Set the working directory inside the container
WORKDIR /app

# Copy all your project files (main.py, etc.) into the container
COPY . .

# Install the Python libraries
# --no-cache-dir keeps the image size smaller
RUN pip install -r ./requirements.txt

# Expose the port the app will run on
EXPOSE 2306

# The command to run when the container starts
# --host 0.0.0.0 is CRITICAL for accessing the server from outside the container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "2306"]