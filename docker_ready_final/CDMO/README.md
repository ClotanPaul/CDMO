# README: Multiple Couriers Problem (MCP) Solver

## Prerequisites

To run the MCP solver, you need to have the following installed on your system:

1. **Docker Desktop**: Ensure Docker Desktop is installed and running on your machine. You can download it from [Docker's official website](https://www.docker.com/products/docker-desktop/).

## Running All Instances

To run all instances with all solvers for all problems, follow these steps:

1. Navigate to the directory containing the `Dockerfile`. This directory is `docker\CDMO`.
2. Build the Docker image by running the following command:
   ```
   docker build -t mcp ./
   ```
   **IMPORTANT**: Make sure you are in the `docker\CDMO` directory when running this command.
3. Once the image is built, run the following command to execute the instances:
   ```
   docker run -it mcp
   ```

## Running a Single Instance

To run a specific instance separately, follow these steps:

1. Navigate to the `docker\CDMO` directory where the `Dockerfile` is located.
2. Build the Docker image using the command:
   ```
   docker build -t mcp ./
   ```
3. Start a Docker container with an interactive shell by running:
   ```
   docker run -it mcp /bin/bash
   ```
4. Inside the container, run the script to execute a specific instance. Use the following command, replacing `[instance number]` with the desired instance:
   ```
   ./run_single_instance.sh [instance number]
   ```
   For example, to run instance 3, use:
   ```
   ./run_single_instance.sh 3
   ```

## Results

The results of the executed instances will be saved in the following directory:

```
docker\CDMO\code\res
```

Alternatively, you can check the results in the docker file at the path:
```
/src/code
```
Under the src folder.

You can access this directory after the Docker container has finished running.

