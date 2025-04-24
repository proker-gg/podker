import docker
import atexit
import uuid
import time
from utils.docker import *


client = docker.from_env()

IMAGE = "python:3.11"


def get_val(id, winnerid):
    if winnerid == 0:
        return "tie"
    if winnerid == id:
        return "win"
    return "loss"


def main():
    print("Create 2 bots")
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

    win_count = [0] * 3

    start = time.time()

    for iteration in range(300):

        request_move_message = {"message": "request_move", "val": None}
        res1 = write_and_read(socket1, request_move_message)["move"]
        res2 = write_and_read(socket2, request_move_message)["move"]

        winner = 0

        res1 = int(res1)
        res2 = int(res2)

        if res1 == res2:
            winner = 0
        elif res2 != (res1 + 1) % 3:
            winner = 1
        else:
            winner = 2

        message1 = {"message": "result", "val": get_val(1, winner)}
        message2 = {"message": "result", "val": get_val(2, winner)}

        write_to_socket(socket1, message1)
        write_to_socket(socket2, message2)

        win_count[winner] += 1

    print(win_count)
    log = read_container_file(container2, "log.txt")
    # print("LOG", log)
    print("TIME ELAPSED", time.time() - start)
    print("Should exit")


atexit.register(clean_up)

if __name__ == "__main__":
    main()
