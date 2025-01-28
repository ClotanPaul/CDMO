FROM minizinc/minizinc:latest

COPY . ./src

WORKDIR /src

RUN apt-get update && apt-get install -y python3 python3-pip python3-venv build-essential libpq-dev glpk-utils

RUN python3 -m pip install -r requirements.txt --break-system-packages

WORKDIR /src/Paul

CMD ["python3", "run_instance.py"]
