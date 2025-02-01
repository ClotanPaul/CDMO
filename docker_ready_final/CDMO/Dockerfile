FROM minizinc/minizinc:2.7.3

COPY . ./src

WORKDIR /src

RUN apt-get update && apt-get install -y python3 python3-pip 
#python3-venv build-essential libpq-dev glpk-utils

RUN python3 -m pip install --no-cache-dir -r requirements.txt
# --break-system-packages

WORKDIR /src/code

CMD ["./run_all.sh"]
