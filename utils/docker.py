import docker
import select
import json
from utils.file import create_tarball

client = docker.from_env()

IMAGE = "python:3.11-alpine"

user_wrapper_code = open("user_wrapper.py", "r").read()


def put_text_as_file(container, script_code, script_name, dir="/"):
    tar_data = create_tarball(script_name, script_code)
    container.put_archive(dir, tar_data)


def start_bot(name, script_code):
    container = client.containers.run(
        IMAGE,
        name=name,
        command="sleep infinity",
        detach=True,
        # use runsc runtime for gVisor
        runtime="runsc",
        mem_limit="128m",
        cpu_period=10000,
        cpu_quota=25000,
        tty=True,
        stdin_open=True,
        auto_remove=True,
    )

    put_text_as_file(
        container=container, script_code=script_code, script_name="user_code.py"
    )
    put_text_as_file(
        container=container, script_code=user_wrapper_code, script_name="wrapper.py"
    )

    exec_id = client.api.exec_create(
        container.id,
        cmd=["python", "/wrapper.py"],
        tty=False,
        stdin=True,
        stdout=True,
        stderr=True,
    )["Id"]

    sock = client.api.exec_start(
        exec_id, tty=False, stream=True, demux=True, socket=True
    )

    return container, sock


def read_line_from_socket(socket, timeout=1000, debug=False):
    stdout_line = b""

    socket = socket._sock

    while True:
        # wait for I/O in socket with timeout
        ready, _, _ = select.select([socket], [], [], timeout / 1000)
        if not ready:
            print("socket timeout")
            return None

        try:
            header = socket.recv(8)
            if not header:
                break
            stream_type = header[0]
            length = int.from_bytes(header[4:], byteorder="big")
            chunk = socket.recv(length)
            if stream_type == 1:
                stdout_line += chunk
                if b"\n" in chunk:
                    break

        except Exception as e:
            print("Error reading output", e)
    if debug:
        print("READ", stdout_line.decode().strip())
    return stdout_line.decode().strip()


def write_to_socket(socket, object):
    message = json.dumps(object) + "\n"
    socket._sock.send(message.encode())


def write_and_read(socket, object, debug=False):
    write_to_socket(socket, object)
    res = json.loads(read_line_from_socket(socket, debug=debug))
    return res


def read_container_file(container, file_name):
    res = container.exec_run(["cat", file_name])
    return res.output.decode()


# we set auto_remove=True, but clean up all containers
def clean_up():
    containers = client.containers.list()
    for container in containers:
        try:
            container.stop()
            container.remove()
        except:
            # catch exception if container is already stopping
            pass
