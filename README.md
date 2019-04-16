# GPU Board Server

## Usage

```
cd server
pip install -r requirements.txt
python main.py
```

docker usage (`nvidia-docker2` package need to be installed):

```shell
docker run --detach --runtime nvidia --pid host \
    --name gpu-board-server \
    --restart always \
    --volume /etc/passwd:/etc/passwd:ro \
    --publish 8000:8000 \
    gpu-board-server
```
