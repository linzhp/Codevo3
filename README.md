# Codevo3
This is the codebase I use for my research on simulating software evolution.

## MSR 2015
If you are interested in replicating the experiments in my MSR 2015 paper, please check out the release [MSR 2015](https://github.com/linzhp/Codevo3/releases/tag/MSR2015).

## Dependencies
* Python 3
* NumPy 1.11
* [Simpy version 3](http://simpy.readthedocs.org/en/3.0.8/)  (simpy v2 fails, even with python3)
* [NetworkX 1.11](https://networkx.github.io/)
* [ply](http://www.dabeaz.com/ply/)
* [plyj (on github)](https://github.com/musiKk/plyj)

On a linux box:
```
sudo apt-get install python3-simpy3
sudo apt-get install python3-networkx
sudo apt-get install ply
git clone https://github.com/musiKk/plyj
cd /path/to/Codevo3
export PYTHONPATH=.:/path/to/plyj/
```

## Running the simulation
Type the following command:

```
env PYTHONPATH=. python3 codevo/simulate.py 200000
```

The number at the end of the command is the number of steps in the simulation. It can be changed. The results are saved in 3 CSV files under `output` directory.

If you are interested in seeing the resulting source code, pass `-s` option to the command line.

## Analysis
The results can be analyzed with R. In `analysis.R`, `get_commit_sizes` takes a `data.table` object read from `output/steps.csv`, and returns a vector of commit sizes. `ggplot.ccdf` plots the CCDF of data stored in a vector.

## Questions, bugs?
Create an issue on this repository, and tag me.
