import asyncio
import socket


async def schedule(delay: int, action: "typing.Callable"):
    task = loop.call_later(
        delay=delay,
        callback=action
    )

    return task


async def run():
    task = loop.create_task(cb())

    while True:
        print('loop')
        await asyncio.sleep(5)

        task.cancel()


async def cb():
    print('cb')
    await asyncio.sleep(2)

    print('end')




loop = asyncio.get_event_loop()

loop.run_until_complete(run())
