import logging
import os
import shutil
import uuid
import shlex

import docker

logger = logging.getLogger(__name__)

LANG_CONFIG = {
    "python": {
        "image": "python:3.12-slim",
        "command": lambda filename, escaped_input: f'sh -c "echo -n {escaped_input} | python {filename}"',
        "filename": "main.py"
    },
    # "javascript": {
    #     "image": "node:20-slim",
    #     "command": lambda filename: f"node {filename}",
    #     "filename": "index.js"
    # },
}
EXEC_TIMEOUT_SECONDS = 20
MEM_LIMIT = "64m"
CPU_SHARES = 512

SHARED_VOLUME_NAME = os.getenv("RUNNER_VOLUME_NAME")
BASE_PATH_IN_WORKER = "/runner_temp"


def execute_code(code: str, language: str = "python", input_data: str = "") -> dict:
    if language not in LANG_CONFIG:
        raise ValueError(f"Unsupported language: {language}")

    config = LANG_CONFIG[language]
    client = docker.from_env()

    run_id = str(uuid.uuid4())
    run_dir_path = os.path.join(BASE_PATH_IN_WORKER, run_id)
    os.makedirs(run_dir_path, exist_ok=True)

    filename = config["filename"]
    host_filepath = os.path.join(run_dir_path, filename)

    with open(host_filepath, "w", encoding="utf-8") as f:
        f.write(code)

    escaped_input = shlex.quote(input_data)

    container_command = config["command"](filename, escaped_input)

    container = None
    try:
        container = client.containers.run(
            image=config["image"],
            command=container_command,
            volumes={SHARED_VOLUME_NAME: {"bind": "/app", "mode": "ro"}},
            working_dir=f"/app/{run_id}",
            mem_limit=MEM_LIMIT,
            cpu_shares=CPU_SHARES,
            network_disabled=True,
            pids_limit=100,
            security_opt=["no-new-privileges"],
            remove=False,
            detach=True,
        )

        if input_data:
            socket = container.attach_socket(params={'stdin': 1, 'stream': 1})
            socket._sock.sendall(input_data.encode('utf-8'))
            socket._sock.close()
            socket.close()

        result = container.wait(timeout=EXEC_TIMEOUT_SECONDS)
        exit_code = result.get("StatusCode", 1)

        stdout = container.logs(stdout=True, stderr=False).decode(
            "utf-8", errors="ignore"
        )
        stderr = container.logs(stdout=False, stderr=True).decode(
            "utf-8", errors="ignore"
        )

        return {
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "timeout": False,
        }

    except docker.errors.ContainerError as e:
        logger.error(f"ContainerError for user code: {e}")
        return {
            "exit_code": e.exit_status,
            "stdout": "",
            "stderr": e.stderr.decode("utf-8", errors="ignore"),
            "timeout": False,
        }
    except Exception as e:
        logger.warning(f"Execution timed out or other exception: {e}")
        if container:
            try:
                container.kill()
            except docker.errors.APIError:
                pass
        return {
            "exit_code": 1,
            "stdout": "",
            "stderr": f"Превышен лимит времени выполнения ({EXEC_TIMEOUT_SECONDS} сек).",
            "timeout": True,
        }
    finally:
        if container:
            try:
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
        if os.path.exists(run_dir_path):
            shutil.rmtree(run_dir_path)
