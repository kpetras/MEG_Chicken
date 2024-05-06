import csv
import os

def extract_and_average_results(directory):
    # Initialize counters for the metrics
    total_hits, total_false_alarms, total_correct_rejections, total_misses = 0, 0, 0, 0
    count = 0

    # List all CSV files in the specified directory
    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]

    for file in csv_files:
        with open(os.path.join(directory, file), mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                total_hits += int(row["Hits"])
                total_false_alarms += int(row["False Alarms"])
                total_correct_rejections += int(row["Correct Rejections"])
                total_misses += int(row["Misses"])
                count += 1

    # Calculate the averages
    avg_hits = total_hits / count if count > 0 else 0
    avg_false_alarms = total_false_alarms / count if count > 0 else 0
    avg_correct_rejections = total_correct_rejections / count if count > 0 else 0
    avg_misses = total_misses / count if count > 0 else 0

    # Print or return the results
    result = {
        "Average Hits": avg_hits,
        "Average False Alarms": avg_false_alarms,
        "Average Correct Rejections": avg_correct_rejections,
        "Average Misses": avg_misses
    }

    return result

# Example usage
directory = "path/to/your/csv/files"  # Replace with your directory path
average_results = extract_and_average_results(directory)
print(average_results)
