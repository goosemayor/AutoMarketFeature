import os
import argparse
import getpass
import multiprocessing
import task_queue
import worker
from pprint import pprint
import yaml
import pandas as pd

def func(config):
    #if not input('pls check (y) or (n):') == 'y': raise Exception('')
    w = worker.Worker(config)
    w.run()


def load_config(filename):
    with open(os.path.join(os.getcwd(), filename), 'rt', encoding='UTF-8') as f:
        config = yaml.load(f)
    return config


def main():
    '''
    Signal backtest
     
    '''

    # args
    parser = argparse.ArgumentParser()
 
    parser.add_argument("-f", "--file", action="store",
                      dest="filename",
                      required=True,
                      help="Alpha configuration file",
                      metavar="yaml")
    

    parser.add_argument("-Q", "--Queue", action="store_true",
                      dest="queue",
                      default=False,
                      required=False,
                      help="lauch queue")
    
    parser.add_argument("-W", "--Worker", action="store_true",
                      dest="worker",
                      default=False,
                      required=False,
                      help="lauch batch")
    


    args = parser.parse_args()  
    args.user = getpass.getuser()

    config = load_config(args.filename)

    if args.queue:
        tq = task_queue.TaskQueue(config)
        tq.timing_run()
        tq.manager.shutdown()
        print('Queue exit.')

    elif args.worker:
        processes_num = config['pool']['processes_num']
        pool = multiprocessing.Pool(processes = processes_num)
        pool.map(func, [config] * processes_num)

        pool.close()
        pool.join()  



if __name__ == '__main__':  
    main()





