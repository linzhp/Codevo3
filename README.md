# Codevo3
This is the codebase I use for my research on simulating software evolution.

## MSR 2015
If you are interested in replicating the experiments in my MSR 2015 paper, please check out the release [MSR 2015](https://github.com/linzhp/Codevo3/releases/tag/MSR2015).

## Dependencies
* Python 3
* [NetworkX](https://networkx.github.io/)
* [plyj](https://github.com/musiKk/plyj), which depends on [ply](http://www.dabeaz.com/ply/)

## Running the simulation
Type the following command:

```
python3 codevo/simulate.py 200000
```

The number at the end of the command is the number of steps in the simulation. It can be changed. The results are saved in 3 CSV files under `output` directory.

If you are interested in seeing the resulting source code, uncomment the last two lines of `codevo/simulate.py` before running the simulation.

## Analysis
The results can be analyzed with R. In `analysis.R`, `get_commit_sizes` takes a `data.table` object read from `output/steps.csv`, and returns a vector of commit sizes. `ggplot.ccdf` plots the CCDF of data stored in a vector.

## Questions, bugs?
Create an issue on this repository, and tag me.
