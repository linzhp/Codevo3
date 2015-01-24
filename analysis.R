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

get_change_sizes <- function(f0, min_fitness) {
  num_steps = nrow(min_fitness)
  min_fitness <- data.table(min_fitness)
  equilibriums <- min_fitness[fitness>=f0, step]
  step_size_file <- file('change_size.txt', 'r')
  step_size <- as.integer(readLines(step_size_file))
  close(step_size_file)
  change_sizes <- vector('integer')
  for (i in 1:length(equilibriums)) {
    size <- 0
    if (i > 1) {
      for (j in (equilibriums[i-1]+1):equilibriums[i]) {
        size <- size + step_size[j]
      }
    } else {
      for (j in 1:equilibriums[i]) {
        size <- size + step_size[j]
      }      
    }
    change_sizes <- c(change_sizes, size)
  }
  change_sizes
}