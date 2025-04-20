import docker
import atexit
import uuid
import select

client = docker.from_env()

IMAGE = "python:3.11"

script_code = open("user_code.py", "r").read()


def start_bot(name="test"):
    container = client.containers.run(
        IMAGE,
        name=name,
        command="sleep infinity",
        detach=True,
        # use runsc runtime for gVisor
        runtime="runsc",
        tty=True,
        stdin_open=True,
        auto_remove=True,
    )

    # Put user script into the container
    # TODO: setup base files + inports in the image
    exec_script = f"echo '''{script_code}''' > /bot_loop.py"
    container.exec_run(["bash", "-c", exec_script])

    exec_id = client.api.exec_create(
        container.id,
        cmd=["python", "/bot_loop.py"],
        tty=False,
        stdin=True,
        stdout=True,
        stderr=True,
    )["Id"]

    sock = client.api.exec_start(
        exec_id, tty=False, stream=True, demux=True, socket=True
    )

    return container, sock


def read_line_from_socket(socket, timeout=300):
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

    return stdout_line.decode().strip()


def main():
    print("Start 5 bots sequentially")

    for i in range(5):
        run_uuid = uuid.uuid4()
        container, socket = start_bot(run_uuid)
        print("started container", run_uuid)
        # socket._sock.send()
        print("Bot:", read_line_from_socket(socket))
        socket.close()

    print("Should exit?")


# we set auto_remove=True, but clean up all containers
def clean_up():
    containers = client.containers.list()
    for container in containers:
        try:
            # throws exception if container is already stopping
            container.stop()
            container.remove()
        except:
            pass


atexit.register(clean_up)

if __name__ == "__main__":
    main()
