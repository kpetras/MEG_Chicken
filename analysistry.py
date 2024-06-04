import pandas as pd
import glob

# Get a list of all CSV files in the current directory
csv_files = glob.glob('*.csv')

# Initialize counters
total_hits = 0
total_fa = 0
total_cr = 0
total_misses = 0
total_files = 0

# Loop through all CSV files
for file in csv_files:
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file)

    # Add up the hits, FA, correct rejections, and misses
    total_hits += df['hits'].mean()
    total_fa += df['FA'].mean()
    total_cr += df['correct rejections'].mean()
    total_misses += df['misses'].mean()

    # Increment the file counter
    total_files += 1

# Calculate the averages
average_hits = total_hits / total_files
average_fa = total_fa / total_files
average_cr = total_cr / total_files
average_misses = total_misses / total_files

# Print the averages
print(f'Average hits: {average_hits}')
print(f'Average FA: {average_fa}')
print(f'Average correct rejections: {average_cr}')
print(f'Average misses: {average_misses}')