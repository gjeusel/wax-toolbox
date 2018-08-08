Profiling
---------

.. automodule:: wax_toolbox.profiling
    :members:

Example usage\:

.. ipython:: python

    import asyncio
    import time
    from concurrent.futures import ThreadPoolExecutor
    from wax_toolbox import profiling

    async def waiter():
        await asyncio.sleep(5)
        return

    def secondwaiter():
        time.sleep(5)
        return

    N = 5

    with profiling.Timer("Asyncio", report_at_enter=True, report_func=print):
        loop = asyncio.get_event_loop()
        asyncio.set_event_loop(loop)
        tasks = []
        for i in range(N):
            tasks.append(asyncio.ensure_future(waiter()))
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

    with profiling.Timer("ThreadPoolExecutor", report_at_enter=True, report_func=print):
        futures = []
        with ThreadPoolExecutor(max_workers=4) as e:  # have you spotted it ?
            for i in range(N):
                futures.append(e.submit(secondwaiter))
        for i in range(len(futures)):
            futures[i].result()
