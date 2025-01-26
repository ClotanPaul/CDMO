# Use a Windows base image with Python and MiniZinc pre-installed
FROM mcr.microsoft.com/windows/nanoserver:ltsc2022

# Set environment variables
ENV CHOCOLATEY_USE_WINDOWS_COMPRESSION=false

# Install Chocolatey and required dependencies
RUN powershell -NoProfile -ExecutionPolicy Bypass -Command \
    Set-ExecutionPolicy Bypass -Scope Process -Force; \
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; \
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Add Chocolatey to PATH
ENV PATH="$PATH:/ProgramData/chocolatey/bin"

# Install MiniZinc and Python via Chocolatey
RUN choco install minizinc --confirm && \
    choco install python --version 3.9 --confirm

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

# Set working directory
WORKDIR /app

# Copy the project into the Docker container
COPY . /app

# Set the entry point for the container
CMD ["powershell"]