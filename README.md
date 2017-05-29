# Codevo3
This is the codebase I use for my research on simulating software evolution.

## MSR 2015
If you are interested in replicating the experiments in my MSR 2015 paper, please check out the release [MSR 2015](https://github.com/linzhp/Codevo3/releases/tag/MSR2015).

## Dependencies
* Python 3
* NumPy 1.12
* [Simpy version 3.0](http://simpy.readthedocs.org/en/latest/)  (simpy v2 fails, even with python3)
* [NetworkX 1.11](https://networkx.github.io/)
* [ply](http://www.dabeaz.com/ply/)
* [plyj](https://github.com/musiKk/plyj)

### Ubuntu

```
sudo apt-get install python3-simpy3 python3-networkx ply
git clone https://github.com/musiKk/plyj
cd /path/to/plyj
cp -r ./plyj ~/.local/lib/python3.6/site-packages
```

Replace `python3.6` in the above command with the actual python version on your machine.

### Windows
Download and install Anaconda 3, which includes Python 3, NumPy, NetworkX. Then:

```
pip install simpy ply
git clone https://github.com/musiKk/plyj
mkdir %APPDATA%\Python\python36\site-packages\plyj
cd \path\to\plyj
xcopy /I .\plyj %APPDATA%\Python\python36\site-packages\plyj
```

Replace `python36` in the above command with the actual python version on your machine.

## Running the simulation
Type the following command:

```
python3 codevo/simulate.py 200000
```

The number at the end of the command is the number of steps in the simulation. It can be changed. The results are saved in 3 CSV files under `output` directory.

If you are interested in seeing the resulting source code, pass `-s` option to the command line.

## Analysis
The results can be analyzed with R. In `analysis.R`, `get_commit_sizes` takes a `data.table` object read from `output/steps.csv`, and returns a vector of commit sizes. `ggplot.ccdf` plots the CCDF of data stored in a vector.

## Questions, bugs?
Create an issue on this repository, and tag me.
