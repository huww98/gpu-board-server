from py3nvml import py3nvml
# import socket
import json
from abc import abstractmethod
# from pprint import pprint
from typing import List, Union
import psutil
from datetime import datetime, timezone


# def get_local_ip() -> str:
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         # doesn't even have to be reachable
#         s.connect(('10.255.255.255', 1))
#         ip = s.getsockname()[0]
#     finally:
#         s.close()
#     return ip


class Serialize:
    @abstractmethod
    def to_json(self) -> Union[list, dict]:
        pass

    @abstractmethod
    def update(self):
        pass


class Memory(Serialize):
    total: int
    free: int
    used: int

    def __init__(self, handle):
        self.handle = handle

    def update(self):
        memory = py3nvml.nvmlDeviceGetMemoryInfo(self.handle)
        self.total = memory.total
        self.free = memory.free
        self.used = memory.used

    def to_json(self) -> Union[list, dict]:
        return {
            'total': self.total,
            'free': self.free,
            'used': self.used
        }


class Utilization(Serialize):
    gpu: int
    memory: int

    def __init__(self, handle):
        self.handle = handle

    def update(self):
        utilization = py3nvml.nvmlDeviceGetUtilizationRates(self.handle)
        self.gpu = utilization.gpu
        self.memory = utilization.memory

    def to_json(self) -> dict:
        return {
            'gpu': self.gpu,
            'memory': self.memory
        }


class Process(Serialize):
    def __init__(self, p):
        self.pid = p.pid
        self.memory = p.usedGpuMemory
        try:
            process = psutil.Process(pid=self.pid)
            self.process_found = True
            self.command = ' '.join(process.cmdline())
            self.username = process.username()
            self.name = process.name()
        except psutil.NoSuchProcess:
            # Sometimes process finishes just before we check
            self.process_found = False

    def to_json(self) -> Union[list, dict]:
        json_content = {
            'pid': self.pid,
            'memory': self.memory,
        }
        if self.process_found:
            json_content.update({
                'name': self.name,
                'command': self.command,
                'username': self.username,
            })
        return json_content


class Processes(Serialize):
    processes: List[Process]

    def __init__(self, handle):
        self.handle = handle

    def update(self):
        self.processes = [
            Process(p) for p in py3nvml.nvmlDeviceGetComputeRunningProcesses(self.handle)
        ]

    def to_json(self) -> Union[list, dict]:
        return [process.to_json() for process in self.processes]


class GpuInfo(Serialize):
    name: str
    memory: Memory

    def __init__(self, index: int):
        self.index = index
        self.handle = py3nvml.nvmlDeviceGetHandleByIndex(index)

        self.name = py3nvml.nvmlDeviceGetName(self.handle)

        self.memory = Memory(self.handle)
        self.utilization = Utilization(self.handle)
        self.processes = Processes(self.handle)

        self.update()

    def update(self):
        self.memory.update()
        self.utilization.update()
        self.processes.update()

    def to_json(self) -> Union[list, dict]:
        return {
            'index': self.index,
            'name': self.name,
            'memory': self.memory.to_json(),
            'utilization': self.utilization.to_json(),
            'processes': self.processes.to_json()
        }


class GpuList(Serialize):
    gpus: List[GpuInfo]

    def __init__(self):
        num_gpus = py3nvml.nvmlDeviceGetCount()
        self.gpus = [GpuInfo(i)
                     for i in range(num_gpus)]

    def update(self):
        for gpu in self.gpus:
            gpu.update()

    def to_json(self) -> Union[list, dict]:
        return [gpu.to_json() for gpu in self.gpus]


class GpuMonitor(Serialize):
    driver_version: str
    gpus: GpuList
    query_time: datetime

    def __init__(self):
        py3nvml.nvmlInit()
        self.driver_version = py3nvml.nvmlSystemGetDriverVersion()
        self.gpus = GpuList()
        self.update()

    def update(self):
        self.query_time = datetime.now(timezone.utc)
        self.gpus.update()

    def to_json(self) -> Union[list, dict]:
        return {
            'driver_version': self.driver_version,
            'gpus': self.gpus.to_json(),
            'query_time': self.query_time.isoformat()
        }

    def close(self):
        py3nvml.nvmlShutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __str__(self):
        pass


if __name__ == '__main__':
    with GpuMonitor() as m:
        m.update()
        # pprint(m.to_json())
        print(json.dumps(m.to_json()))
