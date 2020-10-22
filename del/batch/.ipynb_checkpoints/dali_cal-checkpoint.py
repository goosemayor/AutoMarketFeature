# encoding='utf-8'
import os, sys
import time
import getpass
import yaml

from dali import version
from dali.signal_handler.base import SignalHandler
from dali.signal_handler.operators import *



class Signal(SignalHandler):

    def __init__(self, events_queue, store_path, signal_name, expr, lookback):
        self.signal_name = signal_name
        self.events_queue = events_queue
        self.look_back = lookback
        self.store_path = store_path
        self.expr = expr
        super().__init__()


    def calculate_signal(self):
        OpenPrice = self.open_price
        ClosePrice = self.close_price    
        Volume = self.volume
        VWAP = self.vwap
        Return = self.return_
        HighestPrice = self.high_price
        LowestPrice = self.low_price
        VolChg = self.vol_chg

        s = eval(self.expr)
        s = s[-1] * (s[-1]>0)
        return s 


def Dali_cal(config, expr_dict):
    print('-'*30 + time.strftime('%H:%M') + ' V' + version.__version__ + '-'*30)
    dali_dict = {}
    dali_dict['_id'] = str(expr_dict['_id'])
    dali_dict['expr'] = expr_dict['expr']


    # 删文件夹========================================================================
    store_path = os.path.join(config['output_dir'].replace('~', '/home/%s/' %getpass.getuser()), str(expr_dict['_id']))
    if not os.path.exists(store_path):
        os.mkdir(store_path)

    #try:
    # Queue========================================================================
    from dali.queue import sim_queue
    eq = sim_queue.SimQueue()

    # Signals========================================================================
    init_cash = config['init_cash']
    look_back = config['lookback']
    start_date = config['start_date']
    end_date = config['end_date']

    signal_name = str(expr_dict['_id'])
    signal_list = [signal_name]

    signal_obj = Signal(eq, store_path=store_path,
                                 signal_name=signal_name,
                                 expr=expr_dict['expr'],
                                 lookback=look_back)


    # BarHandler========================================================================
    from dali.price_handler import sim_bar_handler
    barObj = sim_bar_handler.SimBarHandler(config['data_path'].replace('~', '/home/%s/' %getpass.getuser()), eq,
                                start_date=start_date, end_date=end_date, look_back=look_back,
                                store_path=store_path,
                                fill_nan=True)

    # PositionHandler========================================================================
    from dali.position_handler import stock_position_handler
    posObj = stock_position_handler.PositionHandler(price_handler=barObj, init_cash=init_cash,
                               store_path=store_path)

    # Portf========================================================================
    from dali.portfolio_handler import equal_wgts_portfolio_handler
    port = equal_wgts_portfolio_handler.EqualWgtsPortfolioHandler(eq,
                                                signal_list,
                                                 store_path=store_path)

    # ========================================================================
    from dali.order_handler import order_handler
    orderObj = order_handler.OrderHandler(eq, price_handler=barObj, 
                                                position_handler=posObj,
                                                init_cash=init_cash, 
                                                store_path=store_path)

    # ========================================================================
    from dali.execution_handler import sim_exec_handler
    seObj = sim_exec_handler.SimExecHandler(eq, barObj, posObj, store_path=store_path)

    # ========================================================================
    eq.register('BAR', signal_obj)

    eq.register('SIGNAL', port)
    eq.register('PORTFOLIO', orderObj)
    eq.register('ORDER', seObj)
    eq.register('FILL', posObj)
    # ========================================================================
    while not barObj.is_iteration_end():
        barObj.update_bar()
        eq.run()
    # ========================================================================
    eq.unregister('BAR', signal_obj)
    eq.unregister('SIGNAL', port)
    eq.unregister('PORTFOLIO', orderObj)
    eq.unregister('ORDER', seObj)
    eq.unregister('FILL', posObj)



    # ========================================================================
    from dali.statistics import benchmark 
    b = benchmark.Benchmark(account_path=store_path)
    b.run()
    # ========================================================================
    from dali.statistics import trades 
    b = trades.Trades(account_path=store_path)
    b.run()
    # ========================================================================
    from dali.statistics import profiling
    pro = profiling.Profiling(account_path=store_path, benchmark='equal_wgts_benchmark')
    pro.run()
    dali_dict.update(pro.profiles)

    # except Exception as e:
    #     print('[kitkit_cal] raise Exception:%s' %e)
    #     dali_dict['dali_cal_error'] = str(e)

    # with open(os.path.join(store_path, 'dali_profiles.yaml'), 'w') as f:
    #     yaml.dump(dali_dict, f, encoding='unicode', sort_keys=False)

    return dali_dict




