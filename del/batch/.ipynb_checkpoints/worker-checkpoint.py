# coding=utf-8
import time
from datetime import datetime
from pymongo import MongoClient
from multiprocessing import Queue
from multiprocessing.managers import BaseManager
import os
from kitkit_cal import Kitkit_cal
from dali_cal import Dali_cal
import yaml

class QueueManager(BaseManager):
    pass



class Worker():
    def __init__(self, config):
        self.config = config


    # ------------------------连接queue------------------------
    def queue_connect(self):
        QueueManager.register('get_task_queue')
        m = QueueManager(address=(self.config['queue']['host'], self.config['queue']['port']), authkey=b'abc')
        m.connect()
        print('[Auto][Kitkit Worker] queue connected!')
        self.queue = m.get_task_queue()


    # -----------------------从queue获取任务------------------------
    def get_one_task(self):
        value = self.queue.get(True)
        print('[Auto][Kitkit Worker] task acquired %s' %value)
        return value


    # -----------------------连接mongodb------------------------
    def connect_mongodb(self):
        client = MongoClient('mongodb://{0}:{1}@{2}:{3}'.format(self.config['mongodb']['user'],
                                                                self.config['mongodb']['passwd'],
                                                            self.config['mongodb']['host'],
                                                            self.config['mongodb']['port']))
        self.mongodb = client[self.config['mongodb']['db_name']]




    # -----------------------写入mongodb------------------------
    def update_mongodb(self, expr_dict):
        print('[Worker] mongodb update layer:%s _id:%s expr:%s create_date:%s' %(expr_dict['layer'], 
                                                                                 expr_dict['_id'], 
                                                                                 expr_dict['expr'],
                                                                                 expr_dict['create_date']))

        print(expr_dict)
        expr_dict['update_date'] = str(datetime.now())[:19]
        for iterm in expr_dict.keys():
            self.mongodb['%s' %expr_dict['layer']].update_one({'_id': expr_dict['_id']}, {"$set": {iterm: expr_dict[iterm]}})


    # -----------------------写入mongodb------------------------
    # def insert_mongodb(self, expr_dict):
    #     print('[Worker] mongodb update layer:%s _id:%s expr:%s create_date:%s' %(expr_dict['layer'], 
    #                                                                              expr_dict['_id'], 
    #                                                                              expr_dict['expr'],
    #                                                                              expr_dict['create_date']))

    #     self.mongodb['%s' %expr_dict['layer']].insert_one(expr_dict)



    def run(self):
        # 连接队列
        self.queue_connect()
        # 连接数据库
        self.connect_mongodb()
        
        while True:
            # 获取任务
            print('-'*30 + time.strftime('%H:%M') + 'Worker' + '-'*30)
            expr_dict = self.get_one_task()
            if 'kitkit' in self.config:
                kitkit_dict = Kitkit_cal(self.config['kitkit'], expr_dict)
                kitkit_dict['layer'] = expr_dict['layer']
                kitkit_dict['create_date'] = expr_dict['create_date']               
                if self.config['kitkit']['update_mongodb']:
                    self.update_mongodb(kitkit_dict)


            if 'dali' in self.config:
                Dali_cal(self.config['dali'], expr_dict)

            












