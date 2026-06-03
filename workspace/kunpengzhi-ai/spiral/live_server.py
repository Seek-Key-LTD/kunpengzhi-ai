import asyncio
from aiohttp import web

clients = set()

async def stream(request):
    resp = web.StreamResponse(status=200, reason='OK', headers={'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache'})
    await resp.prepare(request)
    clients.add(resp)
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        clients.discard(resp)
    return resp

async def broadcast(data: dict):
    for c in set(clients):
        await c.write(f"data: {data}

".encode())

async def simulate():
    import random
    seats = ['seat_1','seat_2','seat_3','seat_4','seat_5','seat_6','seat_7','seat_8']
    while True:
        seat = random.choice(seats)
        pitch = random.uniform(100, 800)
        await broadcast({"seat_id": seat, "pitch_hz": pitch})
        await asyncio.sleep(0.5)


app = web.Application()
app.router.add_get('/stream', stream)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(simulate())
    web.run_app(app, port=8765)
