import queue
import threading
from threading import Lock

from data_connector import DataConnector
from train_model import train

#DETAILED_GET_RECORDS_DELAY = 86400
DETAILED_GET_RECORDS_DELAY = 1
#DETAILED_RECORD_PROCESSING_DELAY = 86400
DETAILED_RECORD_PROCESSING_DELAY = 1
DETAILED_PROCESSING_BATCH_SIZE = 2

q = queue.Queue()
exit_flag = threading.Event()
millisecs_per_day = 86400000
s_print_lock = Lock()
s_queue_lock = Lock()


def put_queue(d):
    with s_queue_lock:
        q.put(d)


def pop_queue():
    with s_queue_lock:
        d = q.get()
        return d


def get_records():
    from_date = 1590969600000
    to_date = 1591056000000
    index = 0
    print('[get_records] Starting Get Records While Loop')
    while not exit_flag.wait(timeout=DETAILED_GET_RECORDS_DELAY):
        connector = DataConnector(un='admin', pw='Hops@123')
        data = connector.get_data(from_date=from_date, to_date=to_date, index=index)
        if data.shape[0] > 0:
            print('[get_records] Found ' + str(data.shape[0]) + ' records')
            put_queue(data)
            index += 1
        from_date = to_date
        to_date = from_date + millisecs_per_day


def process():
    print('[process] Starting Process While Loop')
    while not exit_flag.wait(timeout=DETAILED_RECORD_PROCESSING_DELAY):
        if q.qsize() >= DETAILED_PROCESSING_BATCH_SIZE:
            count = DETAILED_PROCESSING_BATCH_SIZE
            data = list()
            while count > 0:
                d = pop_queue()
                data.append(d)
                q.task_done()
                count -= 1
            train(data)


def run_d():
    print('[Main] Starting Process Thread')
    thread_process = threading.Thread(target=process)
    print('[Main] Starting Get Records Thread')
    thread_get_records = threading.Thread(target=get_records)
    thread_process.start()
    thread_get_records.start()
    thread_process.join()
    thread_get_records.join()


if __name__ == "__main__":
    print('Inside __main__')
    run_d()
