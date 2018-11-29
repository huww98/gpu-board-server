import asyncio

from gpustat import new_query

import config
import socketio
from sanic import Sanic, response
import ujson

app = Sanic()
sio = socketio.AsyncServer(async_mode='sanic')
sio.attach(app)


@app.route('/')
async def index(request):
    return await response.file('index.html')


async def update_gpu_stats():
    while True:
        await asyncio.sleep(1)
        # print(len(sio.manager.rooms))
        if len(sio.manager.rooms) > 0:
            gpu_stats = new_query()
            # print(gpu_stats.jsonify())
            # gpu_stats_json = ujson.dumps(gpu_stats.jsonify())
            gpu_stats_json = gpu_stats.jsonify()
            gpu_stats_json['query_time'] = gpu_stats_json['query_time'].isoformat()
            await sio.emit('gpustat', gpu_stats_json)
        # print(len(app.sio.rooms))


if __name__ == "__main__":
    app.add_task(update_gpu_stats())
    app.run(host=config.HOST, port=config.PORT)
