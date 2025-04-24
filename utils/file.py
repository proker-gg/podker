import tarfile
import io


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
