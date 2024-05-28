# %%
import os
import csv
from statistics import mean
import numpy as np
from scipy.stats import ttest_ind, ttest_rel


def calculate_averages(files):
    """Calculate the average metrics from a list of CSV files."""
    hits, false_alarms, correct_rejections, misses = [], [], [], []

    for file in files:
        with open(file, mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                hits.append(int(row["Hits"]))
                false_alarms.append(int(row["False Alarms"]))
                correct_rejections.append(int(row["Correct Rejections"]))
                misses.append(int(row["Misses"]))

    return hits, false_alarms, correct_rejections, misses


def extract_and_average_results(directory, folder_name):
    """Calculate the metrics for all trials, first half, and second half."""
    csv_files = [
        os.path.join(directory, folder_name, f)
        for f in os.listdir(os.path.join(directory, folder_name))
        if f.endswith(".csv")
    ]

    # Calculate metrics for all trials
    all_metrics = calculate_averages(csv_files)

    # Calculate metrics for the first half of trials
    halfway_point = len(csv_files) // 2
    first_half_files = csv_files[:halfway_point]
    first_half_metrics = calculate_averages(first_half_files)

    # Calculate metrics for the second half of trials
    second_half_files = csv_files[halfway_point:]
    second_half_metrics = calculate_averages(second_half_files)

    return all_metrics, first_half_metrics, second_half_metrics


def compare_performance(control_metrics, experimental_metrics):
    """Perform Two-sample t-tests between control and experimental groups."""

    def perform_ttest(metric_name, control, experimental):
        t_stat, p_val = ttest_ind(control, experimental)
        print(f"{metric_name} - Two-Sample t-test: t-statistic = {t_stat:.3f}, p-value = {p_val:.3f}")

    control_hits, control_fa, control_cr, control_misses = control_metrics
    exp_hits, exp_fa, exp_cr, exp_misses = experimental_metrics

    perform_ttest("Hits", control_hits, exp_hits)
    perform_ttest("False Alarms", control_fa, exp_fa)
    perform_ttest("Correct Rejections", control_cr, exp_cr)
    perform_ttest("Misses", control_misses, exp_misses)


def compare_initial_final_performance(metrics):
    """Perform Paired-sample t-tests between initial and final trials."""

    def perform_ttest(metric_name, initial, final):
        t_stat, p_val = ttest_rel(initial, final)
        print(f"{metric_name} - Paired t-test: t-statistic = {t_stat:.3f}, p-value = {p_val:.3f}")

    initial_metrics, final_metrics = metrics[1], metrics[2]
    perform_ttest("Hits", initial_metrics[0], final_metrics[0])
    perform_ttest("False Alarms", initial_metrics[1], final_metrics[1])
    perform_ttest("Correct Rejections", initial_metrics[2], final_metrics[2])
    perform_ttest("Misses", initial_metrics[3], final_metrics[3])

# Example usage
control_dir = r"c:\Users\stagaire\Desktop\Repository\MEG_Chicken\control"
experimental_dir = r"c:\Users\stagaire\Desktop\Repository\MEG_Chicken\experimental"

#control_results_bads = extract_and_average_results(control_dir, 'bads_results')
experimental_results_bads = extract_and_average_results(experimental_dir, 'bads_results')

# # Two-sample t-test
# print("\nComparing control vs experimental - Bads:")
# compare_performance(control_results_bads[0], experimental_results_bads[0])

# # Paired-sample t-test
# print("\nComparing initial vs final - Control - Bads:")
# compare_initial_final_performance(control_results_bads)

print("\nComparing initial vs final - Experimental - Bads:")
compare_initial_final_performance(experimental_results_bads)

# control_results_icas = extract_and_average_results(control_dir, 'ICs_results')
# experimental_results_icas = extract_and_average_results(experimental_dir, 'ICs_results')

# # Two-sample t-test
# print("\nComparing control vs experimental - ICs:")
# compare_performance(control_results_icas[0], experimental_results_icas[0])

# # Paired-sample t-test
# print("\nComparing initial vs final - Control - ICs:")
# compare_initial_final_performance(control_results_icas)

# print("\nComparing initial vs final - Experimental - ICs:")
# compare_initial_final_performance(experimental_results_icas)

# %%
import os
import csv
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

def load_results(group, result_type):
    """Load the results from a specified group and type."""
    results = []
    directory = os.path.join(group, f"{result_type}_results")
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            with open(filepath, newline='') as file:
                reader = csv.DictReader(file)
                result = next(reader)
                result = {key: int(value) for key, value in result.items()}
                results.append(result)
    return results

def calculate_d_prime(hits, false_alarms, misses, correct_rejections):
    """Calculate d-prime based on hits, false alarms, misses, and correct rejections."""
    hit_rate = hits / (hits + misses)
    false_alarm_rate = false_alarms / (false_alarms + correct_rejections)

    # Adjust rates to avoid extreme cases
    if hit_rate == 1.0:
        hit_rate = 1 - 1 / (2 * (hits + misses))
    elif hit_rate == 0.0:
        hit_rate = 1 / (2 * (hits + misses))
    
    if false_alarm_rate == 1.0:
        false_alarm_rate = 1 - 1 / (2 * (false_alarms + correct_rejections))
    elif false_alarm_rate == 0.0:
        false_alarm_rate = 1 / (2 * (false_alarms + correct_rejections))

    z_hit = scipy.stats.norm.ppf(hit_rate)
    z_fa = scipy.stats.norm.ppf(false_alarm_rate)
    d_prime = z_hit - z_fa
    return d_prime

def calculate_learning_curve(results, window_size):
    """Calculate the learning curve with sliding time windows."""
    learning_curve = []
    midpoints = []
    for i in range(len(results) - window_size + 1):
        window = results[i:i + window_size]
        d_prime_values = [
            calculate_d_prime(
                result['Hits'], result['False Alarms'],
                result['Misses'], result['Correct Rejections']
            ) for result in window
        ]
        learning_curve.append(np.mean(d_prime_values))
        midpoints.append(i + window_size // 2)
    return learning_curve, midpoints

def plot_learning_curve(control_curve, control_midpoints, experimental_curve, experimental_midpoints, window_size, result_type):
    """Plot the learning curve for both groups."""
    plt.figure()
    if control_curve:
        plt.plot(control_midpoints, control_curve, label='Control')
    if experimental_curve:
        plt.plot(experimental_midpoints, experimental_curve, label='Experimental')
    plt.xlabel('Trial')
    plt.ylabel("d'")
    plt.title(f'Learning Curve ({result_type}, Window Size = {window_size})')
    plt.legend()
    plt.grid(True)
    plt.show()

# Main script

window_size = 2  # Define the sliding window size

# Load results
control_bads = load_results('control', 'bads')
experimental_bads = load_results('experimental', 'bads')
control_ICs = load_results('control', 'ICs')
experimental_ICs = load_results('experimental', 'ICs')

# Calculate learning curves
control_bads_curve, control_bads_midpoints = calculate_learning_curve(control_bads, window_size)
experimental_bads_curve, experimental_bads_midpoints = calculate_learning_curve(experimental_bads, window_size)
control_ICs_curve, control_ICs_midpoints = calculate_learning_curve(control_ICs, window_size)
experimental_ICs_curve, experimental_ICs_midpoints = calculate_learning_curve(experimental_ICs, window_size)

# Plot learning curves
plot_learning_curve(control_bads_curve, control_bads_midpoints, experimental_bads_curve, experimental_bads_midpoints, window_size, 'Bads')
plot_learning_curve(control_ICs_curve, control_ICs_midpoints, experimental_ICs_curve, experimental_ICs_midpoints, window_size, 'ICs')
