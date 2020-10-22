import os
import argparse
import getpass
from pprint import pprint
import yaml
from kitkit_cal import Kitkit_cal
from dali_cal import Dali_cal


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


    expr_dict = {"_id": "test", "expr": "linearreg_slope(exp(geometric_mean(OpenPrice)),150)"}
    if 'kitkit' in config:
        kitkit_expr_dict = Kitkit_cal(config['kitkit'], expr_dict)

    if 'dali' in config:
        Dali_cal(config['dali'], expr_dict)






if __name__ == '__main__':  
    main()
















