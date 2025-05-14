import tarfile
import io
import os


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


def make_tar_directory(source_dir, folder_name="pyker"):
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode="w") as tar:
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.startswith("__"):
                    continue
                full_path = os.path.join(root, file)
                relative_path = "pyker/" + os.path.relpath(full_path, start=source_dir)
                tar.add(full_path, arcname=relative_path)
    tar_stream.seek(0)
    return tar_stream
