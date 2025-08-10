import asyncio

from redis.asyncio import Redis


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, delay: float, name=''):
    while data := await reader.read(1000):
        # print(name, 'received:', data)
        await asyncio.sleep(delay)
        writer.write(data)
        await writer.drain()


class DelayProxy:

    def __init__(self, addr, redis_addr, delay: float):
        self.addr = addr
        self.redis_addr = redis_addr
        self.delay = delay

    async def start(self):
        server = await asyncio.start_server(self.handle, *self.addr)
        asyncio.create_task(server.serve_forever())

    async def handle(self, reader, writer):
        # establish connection to redis
        redis_reader, redis_writer = await asyncio.open_connection(*self.redis_addr)
        pipe1 = asyncio.create_task(pipe(reader, redis_writer, self.delay, 'to redis:'))
        pipe2 = asyncio.create_task(pipe(redis_reader, writer, self.delay, 'from redis:'))
        await asyncio.gather(pipe1, pipe2)


async def main():
    import redis
    print(redis.VERSION)
    print(redis.__file__)

    # create a tcp socket proxy that relays data to Redis and back, inserting 0.1 seconds of delay
    dp = DelayProxy(addr=('localhost', 6380), redis_addr=('localhost', 6379), delay=0.1)
    await dp.start()

    # note that we connect to proxy, rather than to Redis directly
    async with Redis(host='localhost', port=6380) as r:

        await r.set('foo', 'foo')
        await r.set('bar', 'bar')

        t = asyncio.create_task(r.get('foo'))
        await asyncio.sleep(0.050)
        t.cancel()
        try:
            await t
            print('try again, we did not cancel the task in time')
        except asyncio.CancelledError:
            print('managed to cancel the task, connection is left open with unread response')

        print('bar:', await r.get('bar'))
        print('ping:', await r.ping())
        print('foo:', await r.get('foo'))

if __name__ == '__main__':
    asyncio.run(main())

