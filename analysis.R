library(data.table)
library(ggplot2)

get_min_fitness <- function(num_steps, fitness_file) {
  data_file <- file(fitness_file, 'r')
  min_fitness <- vector('numeric', num_steps)
  for (i in 1:num_steps) {
    line <- readLines(data_file, n=1)
    fitness <- unlist(strsplit(line, ',', fixed=TRUE))
    min_fitness[i] <- min(as.numeric(fitness))
  }  
  close(data_file)
  data.frame(step=1:num_steps, fitness=min_fitness)
}

get_change_sizes <- function(f0, min_fitness, step_size_file) {
  num_steps <- nrow(min_fitness)
  min_fitness <- data.table(min_fitness)
  equilibriums <- min_fitness[fitness>=f0, step]
  step_size_file <- file(step_size_file, 'r')
  step_size <- as.integer(readLines(step_size_file))
  close(step_size_file)
  change_sizes <- vector('integer')
  i <- 1
  for (e in equilibriums) {
    size <- 0
    while (i <= e) {
      size <- size + step_size[i]
      i <- i + 1
    }
    change_sizes <- c(change_sizes, size)
  }
  change_sizes <- c(change_sizes, sum(step_size[i:num_steps]))
  change_sizes
}

get_commit_sizes <- function(steps_dt, f0, min_commit_size=1) {
  i <- 1
  commit_sizes <- vector('integer')
  num_steps <- nrow(steps_dt)
  size <- 0
  for (s in 1:num_steps) {
    if (steps_dt[s, min_fitness] >= f0) {
      while (i <= s) {
        size <- size + steps_dt[i, change_size]
        i <- i + 1
      }
      if (size >= min_commit_size) {
        commit_sizes <- c(commit_sizes, size)
        size <- 0        
      }
    }
  }
  c(commit_sizes, size + sum(steps_dt[i:num_steps, change_size]))
}

ggplot.ccdf <- function(data, xlab='x', ylab='CCDF', xbreaks=NULL, ybreaks=NULL) {
  x <- sort(data)
  y <- 1-((1:(length(x))-1)/length(x))
  df <- data.frame(x=x, y=y)
  scale_x <- scale_x_log10()
  if (!is.null(xbreaks)) {
    scale_x <- scale_x_log10(breaks=xbreaks)
  }
  scale_y <- scale_y_log10()
  if (!is.null(ybreaks)) {
    scale_y <- scale_y_log10(breaks=ybreaks)
  }
  qplot(x, y, data=df, xlab=xlab, ylab=ylab) + scale_x + scale_y
}