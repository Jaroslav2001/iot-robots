import asyncio
from typing import Dict, List

from aioserial import AioSerial
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body, BackgroundTasks
from fastapi.responses import HTMLResponse

from connection_manager import ConnectionManager
from get_html import get_html
from setting import serials_ports_names


app = FastAPI()

serials_ports: Dict[str, AioSerial] = {}
manager: ConnectionManager


@app.on_event("startup")
async def startup_event():
    global manager
    for serial_port_name in serials_ports_names:
        serials_ports[serial_port_name] = AioSerial(port=serial_port_name)
    manager = ConnectionManager()


@app.on_event("shutdown")
async def startup_event():
    for serial_port in serials_ports.values():
        serial_port.close()


@app.get("/{port}")
async def get(port: str):
    return HTMLResponse(get_html(port))


async def read_and_print(
    websocket: WebSocket,
    aioserial_instance: AioSerial,
):
    global manager
    while True:
        await manager.broadcast(
            (await aioserial_instance.readline_async()).decode(errors='ignore')
        )


async def write_and_run(
    websocket: WebSocket,
    aioserial_instance: AioSerial
):
    while True:
        await aioserial_instance.write_async(
            bytes(await websocket.receive_text(), 'utf-8')
        )


@app.websocket('/ws/{port}')
async def websocket_endpoint(port: str, websocket: WebSocket):
    if not(port in serials_ports):
        return
    await manager.connect(websocket)
    try:
        tasks = asyncio.gather(
            read_and_print(websocket, serials_ports[port]),
            write_and_run(websocket, serials_ports[port]),
        )
        await tasks
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def status_fun(port: str):
    await serials_ports[port].write_async(
        bytes('r', 'utf-8')
    )

    result: bool = False
    while True:
        message = (await serials_ports[port].readline_async()).decode(errors='ignore')
        try:
            char = int(message[0])
        except Exception:
            continue
        else:
            if char == 0:
                result = False
            if char == 1:
                result = True
            break
    await serials_ports[port].write_async(
        bytes('s', 'utf-8')
    )
    return result


@app.get('/{port}/status')
async def status(port: str):
    return await status_fun(port=port)


async def run_fun(port: str, commands: List[str]):
    while True:
        if not commands:
            break
        await serials_ports[port].write_async(
            bytes(commands[0], 'utf-8')
        )
        print(len(commands))
        while True:
            await asyncio.sleep(1)
            if not await status_fun(port):
                commands.pop(0)
                break


@app.post('/{port}/run')
async def run(
        port: str,
        background_tasks: BackgroundTasks,
        commands: List[str] = Body(...),
):
    background_tasks.add_task(run_fun, port, commands)
    return True
