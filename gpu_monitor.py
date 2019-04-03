from py3nvml import py3nvml
import socket
import json
from abc import abstractmethod
from pprint import pprint
from typing import List, Union
import psutil


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
        process = psutil.Process(pid=self.pid)
        self.command = ' '.join(process.cmdline())
        self.username = process.username()
        # print(' '.join(process.cmdline()))

    def to_json(self) -> Union[list, dict]:
        return {
            'pid': self.pid,
            'memory': self.memory,
            'command': self.command,
            'username': self.username,
        }


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

    def __init__(self, handle):
        self.handle = handle

        self.name = py3nvml.nvmlDeviceGetName(handle)

        self.memory = Memory(handle)
        self.utilization = Utilization(handle)
        self.processes = Processes(handle)

        self.update()

    def update(self):
        self.memory.update()
        self.utilization.update()
        self.processes.update()

    def to_json(self) -> Union[list, dict]:
        return {
            'name': self.name,
            'memory': self.memory.to_json(),
            'utilization': self.utilization.to_json(),
            'processes': self.processes.to_json()
        }


class GpuList(Serialize):
    gpus: List[GpuInfo]

    def __init__(self):
        num_gpus = py3nvml.nvmlDeviceGetCount()
        self.gpus = [GpuInfo(py3nvml.nvmlDeviceGetHandleByIndex(i)) for i in range(num_gpus)]

    def update(self):
        for gpu in self.gpus:
            gpu.update()

    def to_json(self) -> Union[list, dict]:
        return [gpu.to_json() for gpu in self.gpus]


class GpuMonitor(Serialize):
    driver_version: str
    gpus: GpuList

    def __init__(self):
        py3nvml.nvmlInit()
        self.driver_version = py3nvml.nvmlSystemGetDriverVersion()
        self.gpus = GpuList()
        self.update()

    def update(self):
        self.gpus.update()

    def to_json(self) -> Union[list, dict]:
        return {
            'driver_version': self.driver_version,
            'gpus': self.gpus.to_json()
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
        pprint(m.to_json())
        print(json.dumps(m.to_json()))
