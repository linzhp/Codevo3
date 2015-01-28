library(data.table)

get_min_fitness <- function(num_steps) {
  data_file <- file('output/fitness.txt', 'r')
  min_fitness <- vector('numeric', num_steps)
  for (i in 1:num_steps) {
    line <- readLines(data_file, n=1)
    fitness <- unlist(strsplit(line, ',', fixed=TRUE))
    min_fitness[i] <- min(as.numeric(fitness))
  }  
  close(data_file)
  data.frame(step=1:num_steps, fitness=min_fitness)
}

get_change_sizes <- function(f0, min_fitness) {
  num_steps <- nrow(min_fitness)
  min_fitness <- data.table(min_fitness)
  equilibriums <- min_fitness[fitness>=f0, step]
  step_size_file <- file('output/change_size.txt', 'r')
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