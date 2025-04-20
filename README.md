# Podker

Demo of a single pod to sandbox user poker bots using gVisor.

### Local Development 


1. Install [gVisor](https://gvisor.dev/docs/user_guide/install/) (Linux only). Alternatively comment out `runtime="runsc"` for docker images ⚠️ Local dev only ⚠️.
2. Install the [uv](https://pypi.org/project/uv/0.1.16/) package manager.
3. If applicable, give user docker permissions: `sudo usermod -aG docker $USER && newgrp docker`
4. `uv run main.py`


### Development with Docker

- TODO
