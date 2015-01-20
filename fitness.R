library(data.table)

get_min_fitness <- function(num_steps) {
  data_file <- file('fitness.txt', 'r')
  min_fitness <- vector('numeric', num_steps)
  for (i in 1:num_steps) {
    line <- readLines(data_file, n=1)
    fitness <- unlist(strsplit(line, ',', fixed=TRUE))
    min_fitness[i] <- min(as.numeric(fitness))
  }  
  close(data_file)
  data.frame(step=1:num_steps, fitness=min_fitness)
}

get_avalanche_sizes <- function(f0, min_fitness) {
  num_steps = nrow(min_fitness)
  min_fitness <- data.table(min_fitness)
  equilibriums <- min_fitness[fitness>=f0, step]
  avalanche_sizes <- if(equilibriums[1] - 1 > 0) equilibriums[1] - 1 else vector('integer')
  for (i in 2:length(equilibriums)) {
    size <- equilibriums[i] - equilibriums[i-1]
    if (size > 0) {
      avalanche_sizes <- c(avalanche_sizes, size)
    }
  }
  avalanche_sizes
}