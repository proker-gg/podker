import docker
import atexit
import uuid
import select
import time
import json
import io
import tarfile


def create_tarball(file_name, file_content):
    """
    Create an in-memory tar archive containing one file.

    Args:
        file_name: Name of the file inside the container (e.g., "bot_loop.py")
        file_content: String content of the file

    Returns:
        Bytes of the tar archive
    """
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        data = file_content.encode()
        tarinfo = tarfile.TarInfo(name=file_name)
        tarinfo.size = len(data)
        tar.addfile(tarinfo, io.BytesIO(data))
    tar_stream.seek(0)
    return tar_stream


client = docker.from_env()

IMAGE = "python:3.11"


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

    # Put user script into the container
    # TODO: setup base files + inports in the image
    tar_data = create_tarball("bot_loop.py", script_code)
    container.put_archive("/", tar_data)
    # exec_script = f"echo '''{script_code}''' > /bot_loop.py"
    # container.exec_run(["bash", "-c", exec_script])

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


def read_line_from_socket(socket, timeout=1000):
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


BEATS = [2, 0, 1]


def get_val(id, winnerid):
    if winnerid == 0:
        return "tie"
    if winnerid == id:
        return "win"
    return "loss"


def main():
    print("Last 2 bots")

    num_bots = 2
    start = time.time()

    script_code1 = open("user_code.py", "r").read()

    script_code2 = open("user_code_2.py", "r").read()

    run_uuid1 = uuid.uuid4()
    container1, socket1 = start_bot(run_uuid1, script_code1)

    run_uuid2 = uuid.uuid4()
    container2, socket2 = start_bot(run_uuid2, script_code2)

    message = read_line_from_socket(socket1)
    message = read_line_from_socket(socket2)
    print("REC", message)
    print("started containers", time.time() - start, "seconds")

    # for i in range(10):
    #     request_move_message = {"message": "echo", "val": None}
    #     message = json.dumps(request_move_message) + "\n"
    #     socket1._sock.send(message.encode())
    #     print(read_line_from_socket(socket1))

    win_count = [0] * 3

    start = time.time()

    for iteration in range(30000):
        request_move_message = {"message": "request_move", "val": None}
        message = json.dumps(request_move_message) + "\n"
        socket1._sock.send(message.encode())
        socket2._sock.send(message.encode())

        res1 = json.loads(read_line_from_socket(socket1))["move"]
        res2 = json.loads(read_line_from_socket(socket2))["move"]

        # print("ASDAS", res1, res2)

        status = []
        winner = 0

        res1 = int(res1)
        res2 = int(res2)

        if res1 == res2:
            winner = 0
        elif BEATS[res1] == res2:
            winner = 1
        else:
            winner = 2

        message1 = json.dumps({"message": "result", "val": get_val(1, winner)}) + "\n"
        message2 = json.dumps({"message": "result", "val": get_val(2, winner)}) + "\n"
        socket1._sock.send(message1.encode())
        socket2._sock.send(message2.encode())

        win_count[winner] += 1

    print(win_count)
    res = container2.exec_run(["cat", "log.txt"])
    # print("LOG", res.output.decode())
    print("TIME ELAPSED", time.time() - start)
    print("Should exit")


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
