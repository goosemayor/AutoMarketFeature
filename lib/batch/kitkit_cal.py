# coding=utf-8
import os, sys
import time
import numpy as np
import pandas as pd
from copy import copy
import getpass
import yaml

from kitkit import version
from kitkit.operators import *
from kitkit.data import pricevolume, resample, clean
from kitkit.traders import vwap_deal
from kitkit.evaluators import benchmark_alpha_perform, quintiles_alpha_perform


class Alpha():    

    def build(self, data, expr) : 
        ClosePrice = data.ClosePrice    
        Volume = data.Volume
        OpenPrice = data.OpenPrice
        Return = data.Return
        VWAP = data.VWAP
        HighestPrice = data.HighestPrice
        LowestPrice = data.LowestPrice
        VolChg = data.VolChg

        s = eval(expr)
        return np.abs(s)




def Kitkit_cal(config, expr_dict):
    print('-'*30 + time.strftime('%H:%M') + ' V' + version.__version__ + '-'*30)
    kitkit_dict = {}
    kitkit_dict['_id'] = expr_dict['_id']
    kitkit_dict['expr'] = expr_dict['expr']

    # config
    price_path = config['data_path'].replace('~', '/home/%s/' %getpass.getuser())
    IS_start= config['resample_start']
    IS_end = config['resample_end']
    look_back  = config['lookback']
    commission = config['commission']
    cycle = config['cycle']
    quintiles_num = config['quintiles_num']
    output_dir = config['output_dir'] 
    if output_dir is not None:
        output_dir = os.path.join(config['output_dir'].replace('~', '/home/%s/' %getpass.getuser()), str(expr_dict['_id']))
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
    kitkit_dict.update(config)

    try:
        # data
        pv = pricevolume.PriceVolume(path=price_path)
        pv.build()

        # resample
        rs = resample.Resample(IS_start=IS_start, IS_end=IS_end)
        IS_Data, OOS_Data = rs.build(pv)
        rs = clean.Clean()
        IS_Data = rs.build(IS_Data)

        # expr
        alpha = Alpha()
        alpha = alpha.build(IS_Data, kitkit_dict['expr'])
        alpha = pd.DataFrame(alpha).fillna(0).values
        alpha = alpha * (alpha >0)

        # deal 
        p= vwap_deal.VWAPDeal(IS_Data, alpha, look_back, output_dir=output_dir)
        p.build()

        # benchmark perf
        ap = benchmark_alpha_perform.BechmarkAlphaPerform(p, commission=commission, cycle=cycle, figure=True, output_dir=output_dir)
        ap.build()
        kitkit_dict.update(ap.indicators)

        # quintiles perf
        ap = quintiles_alpha_perform.QuintilesAlphaPerform(p, quintiles_num=quintiles_num, commission=commission, cycle=cycle, figure=True, output_dir=output_dir)
        ap.build()

        kitkit_dict['cal_error'] = None
        for i in config['complete_mark']:
            kitkit_dict[i] = config['complete_mark'][i]

    except Exception as e:
        print('[kitkit_cal] raise Exception:%s' %e)
        kitkit_dict['kitkit_cal_error'] = str(e)

    kitkit_dict.update(ap.indicators)
    if output_dir is not None:
        save_kitkit_dict = copy(kitkit_dict)
        save_kitkit_dict['_id'] = str(save_kitkit_dict['_id'])
        with open(os.path.join(output_dir, 'kitkit_profiles.yaml'), 'w') as f:
            yaml.dump(save_kitkit_dict, f, encoding='unicode', sort_keys=False)

    return kitkit_dict



    