import time

from celery import shared_task


@shared_task
def panhandler_test(count: int) -> str:
    i = 0
    while i < count:
        print(f'{i}')
        time.sleep(0.1)
        i = i + 1

    return f'Counted up to {count}'
