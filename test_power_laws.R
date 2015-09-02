source('analysis.R')
test_all_power_laws <- function(run) {
  print(paste0('Run #', run))
  steps <- fread(paste0('output', run, '/steps.csv'))
  commit_sizes <- get_commit_sizes(steps, 0.77)
  print(paste('Commit size:', test_power_law(commit_sizes)))
  methods <- fread(paste0('output', run, '/references.csv'))
  print(paste('Method calls:', test_power_law(methods$ref_count+1)))
  classes <- fread(paste0('output', run, '/classes.csv'))
  print(paste('Class size', test_power_law(classes$lines)))
  print(paste('Class degree:', test_power_law(classes$degree+1)))
}


for (i in 1:20) {
  test_all_power_laws(i)
}
