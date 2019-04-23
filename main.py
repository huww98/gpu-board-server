import asyncio
import logging
from signal import signal, SIGINT

import socketio
from sanic import Sanic
from gpu_monitor import GpuMonitor

import config

app = Sanic()
sio = socketio.AsyncServer(async_mode='sanic')
sio.attach(app)

MAX_FAIL_IN_A_ROW = 5

async def update_gpu_stats():
    gm = None
    fail_in_a_row = 0
    logger = logging.getLogger("update_gpu_stats")
    while True:
        await asyncio.sleep(1)
        # Query for gpustat only when there's one more in room
        if len(sio.manager.rooms) > 0:
            try:
                if gm is None:
                    gm = GpuMonitor()

                gm.update()
                gpu_stats = gm.to_json()

                await sio.emit('gpustat', gpu_stats)
                fail_in_a_row = 0
            except:
                fail_in_a_row += 1
                logger.error("Exception while retriving new status. fail in a row: %d", fail_in_a_row, exc_info=True)
                if fail_in_a_row >= MAX_FAIL_IN_A_ROW:
                    logger.error("Too many fail in a row, exiting")
                    break
        else:
            if gm is not None:
                gm.close()
                gm = None

if __name__ == "__main__":
    server = app.create_server(host=config.HOST, port=config.PORT, return_asyncio_server=True)
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(server)
    signal(SIGINT, lambda s, f: loop.stop())
    try:
        loop.run_until_complete(update_gpu_stats())
    except KeyboardInterrupt:
        loop.stop()
