# coding=utf-8
from multiprocessing import Queue
from multiprocessing.managers import BaseManager
import os, time, sys
import numpy as np

from pymongo import MongoClient
from lib import version



class QueueManager(BaseManager):
    pass


class TaskQueue():
    def __init__(self, config):
        self.config = config
        self.init_queue()


    def init_queue(self):
        self.queue = Queue(maxsize=self.config['queue']['queue_size'])
        QueueManager.register('get_task_queue', callable=lambda: self.queue)
        manager = QueueManager(address=('', self.config['queue']['port']), authkey=b'abc')
        manager.start()
        self.queue_task = manager.get_task_queue()


    def connect_mongodb(self):
        client = MongoClient('mongodb://{0}:{1}@{2}:{3}'.format(self.config['mongodb']['user'],
                                                                self.config['mongodb']['passwd'],
                                                            self.config['mongodb']['host'],
                                                            self.config['mongodb']['port']))
        db = client[self.config['mongodb']['db_name']]
        return db


    def write_queue(self, q, value):
        q.put(value)


    def update_queue(self, data_set):
        for d in data_set:
            self.write_queue(self.queue_task, d)


    def fetch_data(self, col, col_name):
        # 提取数据，优先级降序排列
        #return col.find({"IS_backtest": "Undo"}).sort("priority", pymongo.DESCENDING)[0:data_num]
        print('[Auto][TaskQueue] %s.%s.find(%s)' %(self.config['mongodb']['db_name'], col_name,
                                                     self.config['mongodb']['query']))
        return col.find(self.config['mongodb']['query'])[0:self.config['queue']['queue_size']]


    def timing_run(self):
        from collections import deque
        q_num = deque([], maxlen=10)
        q_time = deque([], maxlen=10)
        while True:
            if self.queue.qsize() <= self.config['queue']['queue_threshold']:
                q_num = deque([], maxlen=10)
                q_time = deque([], maxlen=10)
                db = self.connect_mongodb()
                for i in self.config['mongodb']['db_collection']:
                    dataset = self.fetch_data(db[i], i)
                    if dataset.count() == 0:
                        print('[Auto][TaskQueue] collection:%s No data fetched from' %i)
                        time.sleep(2)
                    else:
                        print('[Auto][TaskQueue] update_queue...')
                        self.update_queue(dataset)
                        time.sleep(2)
                        break
                    
            else:
                q_num.append(self.queue.qsize())
                q_time.append(time.time())
                bar_length = 10
                percent = 1. * self.queue.qsize() / self.config['queue']['queue_size']
                hashes = '#' * int(percent * bar_length)
                spaces = ' ' * (bar_length - len(hashes))
                sys.stdout.write("\r[Auto][TaskQueue][%s][V%s][%s][%s][%s/%s][%s] %d%% (%s/s)" % (time.strftime('%H:%M'),
                                                                        version.__version__ .replace("\"",""), self.config['mongodb']['db_name'], i,
                                                                      self.queue.qsize(), self.config['queue']['queue_size'],
                                                                       hashes + spaces, percent * 100,
                                                                       np.round((q_num[0]-q_num[-1])/(q_time[-1]-q_time[0]+1e-10), 2)))
                sys.stdout.flush()
                time.sleep(0.5)





    