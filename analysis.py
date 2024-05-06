
# %%
import os
import csv
from statistics import mean

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

    avg_hits = mean(hits) if hits else 0
    avg_false_alarms = mean(false_alarms) if false_alarms else 0
    avg_correct_rejections = mean(correct_rejections) if correct_rejections else 0
    avg_misses = mean(misses) if misses else 0

    result = {
        "Average Hits": avg_hits,
        "Average False Alarms": avg_false_alarms,
        "Average Correct Rejections": avg_correct_rejections,
        "Average Misses": avg_misses
    }

    return result

def extract_and_average_results(directory, suffix):
    """Calculate the average metrics for all trials, first half, and second half."""
    csv_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(suffix)]

    # Calculate the averages for all trials
    all_averages = calculate_averages(csv_files)

    # Calculate the averages for the first half of trials
    halfway_point = len(csv_files) // 2
    first_half_files = csv_files[:halfway_point]
    first_half_averages = calculate_averages(first_half_files)

    # Calculate the averages for the second half of trials
    second_half_files = csv_files[halfway_point:]
    second_half_averages = calculate_averages(second_half_files)

    result = {
        "All Trials": all_averages,
        "First Half": first_half_averages,
        "Second Half": second_half_averages
    }

    return result

# Example usage
directory = r"c:\Users\stagaire\Desktop\Repository\MEG_Chicken"

average_results_bads = extract_and_average_results(directory, 'bads_results.csv')
average_results_ICs = extract_and_average_results(directory, 'ICs_results.csv')

print("Average results for bads:", average_results_bads)
print("Average results for ICs:", average_results_ICs)

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

control_results_bads = extract_and_average_results(control_dir, 'bads_results')
experimental_results_bads = extract_and_average_results(experimental_dir, 'bads_results')

# Two-sample t-test
print("\nComparing control vs experimental - Bads:")
compare_performance(control_results_bads[0], experimental_results_bads[0])

# Paired-sample t-test
print("\nComparing initial vs final - Control - Bads:")
compare_initial_final_performance(control_results_bads)

print("\nComparing initial vs final - Experimental - Bads:")
compare_initial_final_performance(experimental_results_bads)

control_results_icas = extract_and_average_results(control_dir, 'ICs_results')
experimental_results_icas = extract_and_average_results(experimental_dir, 'ICs_results')

# Two-sample t-test
print("\nComparing control vs experimental - ICs:")
compare_performance(control_results_icas[0], experimental_results_icas[0])

# Paired-sample t-test
print("\nComparing initial vs final - Control - ICs:")
compare_initial_final_performance(control_results_icas)

print("\nComparing initial vs final - Experimental - ICs:")
compare_initial_final_performance(experimental_results_icas)

# %%
