import os
import sys
import logging
import random
import simpy
from time import time
from argparse import ArgumentParser

from codevo import Codebase
from codevo.team import Manager

if __name__ == '__main__':
    arg_parser = ArgumentParser(description='Run the simulation')
    arg_parser.add_argument('-o', dest='output_dir', type=str, default='output', help='output directory')
    arg_parser.add_argument('time', metavar='N', type=int, help='simulation time')
    arg_parser.add_argument('-s', dest='save_source', action='store_true',
                            help='whether to save the Java source code')
    options = arg_parser.parse_args(sys.argv[1:])
    if os.path.exists(options.output_dir):
        for root, dirs, files in os.walk(options.output_dir):
            for name in files:
                os.remove(os.path.join(root, name))
    else:
        os.makedirs(options.output_dir)
    if options.save_source:
        os.makedirs(os.path.join(options.output_dir, 'src'), exist_ok=True)
    random_seed = round(time())
    print('Using seed', random_seed)
    random.seed(random_seed)
    # logging.basicConfig(level=logging.INFO)
    env = simpy.Environment()
    codebase = Codebase()
    m = Manager(env, codebase)
    env.run(until=options.time)
    print('Number of developers: ', len(m.developers))
    codebase.save(options.output_dir, options.save_source)