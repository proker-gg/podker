import uuid
import json

from utils.docker import (
    start_bot,
    read_line_from_socket,
    write_and_read,
    write_to_socket,
    read_container_file,
)

"""
Player class to abstract socker and docker logic from game logic
"""


class Player:
    def __init__(self, id, player_code, user="unknown", revision="1"):
        # ready status??
        self.status = ""
        self.id = id
        self.user = user
        self.revision = revision

        # start container with user_code
        self.player_uuid = uuid.uuid4()
        container, socket = start_bot(self.player_uuid, player_code)

        self.container = container
        self.socket = socket

        # 2 seconds to send init message
        init_message = self.read(timeout=1000, debug=True)

        # handle failed to start
        # if not init_message:
        print(id, init_message)

    def read(self, timeout=1000, debug=False):
        # json or None
        res = read_line_from_socket(self.socket, timeout=timeout, debug=debug)
        return res

    def send(self, message):
        write_to_socket(self.socket, object=message)

    def send_and_read(self, message, debug=False):
        return write_and_read(self.socket, message, debug=debug)

    def read_logs(self):
        return read_container_file(self.container, "log.txt")

    def clean_up(self):
        self.container.stop()
        self.container.remove()
        self.socket.close()
