import pandas as pd
import glob
import matplotlib.pyplot as plt 
from scipy import stats

# Calculate averages for each participant in the control group and averages accross the control group
# Calculate averages for each participant in the experimental group and averages accross the experimental group

def calculate_averages(directory):
    # Get a list of all CSV files in the specified directory that start with 'results'
    csv_files = glob.glob(f'{directory}/results*.csv')

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

        # Calculate and print the averages for this file
        print(f'{file} averages:')
        print(f'Average hits: {df["hits"].mean()}')
        print(f'Average FA: {df["false_alarms"].mean()}')
        print(f'Average correct rejections: {df["correct_rejections"].mean()}')
        print(f'Average misses: {df["misses"].mean()}')
        print()

        # Add up the hits, FA, correct rejections, and misses for the overall averages
        total_hits += df['hits'].mean()
        total_fa += df['false_alarms'].mean()
        total_cr += df['correct_rejections'].mean()
        total_misses += df['misses'].mean()

        # Increment the file counter
        total_files += 1

    # Calculate the overall averages
    average_hits = total_hits / total_files
    average_fa = total_fa / total_files
    average_cr = total_cr / total_files
    average_misses = total_misses / total_files

    # Print the overall averages
    print(f'{directory} overall averages:')
    print(f'Average hits: {average_hits}')
    print(f'Average FA: {average_fa}')
    print(f'Average correct rejections: {average_cr}')
    print(f'Average misses: {average_misses}')
    print()

    return average_hits, average_fa, average_cr, average_misses

# Calculate averages for 'control' and 'experimental' directories
control_averages = calculate_averages('control')
experimental_averages = calculate_averages('experimental')

# Plot the averages
labels = ['Hits', 'False Alarms', 'Correct Rejections', 'Misses']
x = range(len(labels))

plt.bar(x, control_averages, width=0.4, label='Control', color='b', align='center')
plt.bar(x, experimental_averages, width=0.4, label='Experimental', color='r', align='edge')

plt.xlabel('Metric')
plt.ylabel('Average')
plt.title('Comparison of Averages')
plt.xticks(x, labels)
plt.legend()
plt.show()

# Calculate averages of the first half of trials and the second half for each participant in the control group and averages of the first and second half of trials accross the control group
# Calculate averages of the first half of trials and the second half for each participant in the experimental group and averages of the first and second half of trials accross the experimental group

def calculate_averages(directory):
    # Get a list of all CSV files in the specified directory that start with 'results'
    csv_files = glob.glob(f'{directory}/results*.csv')

    # Initialize counters for first and second half
    total_hits_first_half = 0
    total_fa_first_half = 0
    total_cr_first_half = 0
    total_misses_first_half = 0

    total_hits_second_half = 0
    total_fa_second_half = 0
    total_cr_second_half = 0
    total_misses_second_half = 0

    total_files = 0

    # Loop through all CSV files
    for file in csv_files:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file)

        # Split the DataFrame into two halves
        first_half = df[df['trial'] <= df['trial'].median()]
        second_half = df[df['trial'] > df['trial'].median()]

        # Calculate and print the averages for this file
        print(f'{file} averages:')
        print('First half:')
        print(f'Average hits: {first_half["hits"].mean()}')
        print(f'Average FA: {first_half["false_alarms"].mean()}')
        print(f'Average correct rejections: {first_half["correct_rejections"].mean()}')
        print(f'Average misses: {first_half["misses"].mean()}')
        print('Second half:')
        print(f'Average hits: {second_half["hits"].mean()}')
        print(f'Average FA: {second_half["false_alarms"].mean()}')
        print(f'Average correct rejections: {second_half["correct_rejections"].mean()}')
        print(f'Average misses: {second_half["misses"].mean()}')
        print()

        # Add up the hits, FA, correct rejections, and misses for the overall averages
        total_hits_first_half += first_half['hits'].mean()
        total_fa_first_half += first_half['false_alarms'].mean()
        total_cr_first_half += first_half['correct_rejections'].mean()
        total_misses_first_half += first_half['misses'].mean()

        total_hits_second_half += second_half['hits'].mean()
        total_fa_second_half += second_half['false_alarms'].mean()
        total_cr_second_half += second_half['correct_rejections'].mean()
        total_misses_second_half += second_half['misses'].mean()

        # Increment the file counter
        total_files += 1

    # Calculate the overall averages
    average_hits_first_half = total_hits_first_half / total_files
    average_fa_first_half = total_fa_first_half / total_files
    average_cr_first_half = total_cr_first_half / total_files
    average_misses_first_half = total_misses_first_half / total_files

    average_hits_second_half = total_hits_second_half / total_files
    average_fa_second_half = total_fa_second_half / total_files
    average_cr_second_half = total_cr_second_half / total_files
    average_misses_second_half = total_misses_second_half / total_files

    # Print the overall averages
    print(f'{directory} overall averages:')
    print('First half:')
    print(f'Average hits: {average_hits_first_half}')
    print(f'Average FA: {average_fa_first_half}')
    print(f'Average correct rejections: {average_cr_first_half}')
    print(f'Average misses: {average_misses_first_half}')
    print('Second half:')
    print(f'Average hits: {average_hits_second_half}')
    print(f'Average FA: {average_fa_second_half}')
    print(f'Average correct rejections: {average_cr_second_half}')
    print(f'Average misses: {average_misses_second_half}')
    print()

# Calculate averages for 'control' and 'experimental' directories
calculate_averages('control')
calculate_averages('experimental')

# %%
# Learning curve
import pandas as pd
import glob
import matplotlib.pyplot as plt
import numpy as np

def calculate_averages_and_plot(directory):
    csv_files = glob.glob(f'{directory}/results*.csv')

    all_correct_responses = []

    for file in csv_files:
        df = pd.read_csv(file)
        df['correct_responses'] = df['hits'] + df['correct_rejections']
        correct_responses = []

        for i in range(0, len(df), 10):
            window = df[i:i+10]
            correct_responses.append(window['correct_responses'].mean())

        all_correct_responses.append(correct_responses)

    # Make all lists in all_correct_responses the same length
    max_length = max(map(len, all_correct_responses))
    all_correct_responses = [cr + [np.nan]*(max_length-len(cr)) for cr in all_correct_responses]

    # Calculate the average of correct responses across trials
    avg_correct_responses = np.nanmean(all_correct_responses, axis=0)

    plt.plot(avg_correct_responses, label=directory)

# Calculate averages for 'control' and 'experimental' directories
calculate_averages_and_plot('control')
calculate_averages_and_plot('experimental')

plt.xlabel('Time window (10 trials each)')
plt.ylabel('Average correct responses')
plt.title('Learning curve')
plt.legend()
plt.show()
# %%
from scipy import stats

def calculate_averages(directory):
    csv_files = glob.glob(f'{directory}/results*.csv')

    averages_hits = []
    averages_fa = []
    averages_cr = []
    averages_misses = []

    for file in csv_files:
        df = pd.read_csv(file)
        averages_hits.append(df['hits'].mean())
        averages_fa.append(df['false_alarms'].mean())
        averages_cr.append(df['correct_rejections'].mean())
        averages_misses.append(df['misses'].mean())

    return averages_hits, averages_fa, averages_cr, averages_misses

# Calculate averages for 'control' and 'experimental' directories
control_averages = calculate_averages('control')
experimental_averages = calculate_averages('experimental')

# Perform t-tests
t_test_hits = stats.ttest_ind(control_averages[0], experimental_averages[0])
t_test_fa = stats.ttest_ind(control_averages[1], experimental_averages[1])
t_test_cr = stats.ttest_ind(control_averages[2], experimental_averages[2])
t_test_misses = stats.ttest_ind(control_averages[3], experimental_averages[3])

print(f'T-test results:')
print(f'Hits: {t_test_hits}')
print(f'False Alarms: {t_test_fa}')
print(f'Correct Rejections: {t_test_cr}')
print(f'Misses: {t_test_misses}')
# %%
def calculate_averages(directory):
    csv_files = glob.glob(f'{directory}/results*.csv')

    averages_hits = []
    averages_fa = []
    averages_cr = []
    averages_misses = []

    for file in csv_files:
        df = pd.read_csv(file)
        last_10_trials = df.tail(10)  # Select the last 10 trials

        print(f'Last 10 trials for file {file}:')
        print(last_10_trials)

        averages_hits.append(last_10_trials['hits'].mean())
        averages_fa.append(last_10_trials['false_alarms'].mean())
        averages_cr.append(last_10_trials['correct_rejections'].mean())
        averages_misses.append(last_10_trials['misses'].mean())

    # Calculate the overall averages for the last 10 trials across all files
    overall_average_hits = sum(averages_hits) / len(averages_hits)
    overall_average_fa = sum(averages_fa) / len(averages_fa)
    overall_average_cr = sum(averages_cr) / len(averages_cr)
    overall_average_misses = sum(averages_misses) / len(averages_misses)

    return overall_average_hits, overall_average_fa, overall_average_cr, overall_average_misses

# Calculate averages for 'control' and 'experimental' directories
control_averages = calculate_averages('control')
experimental_averages = calculate_averages('experimental')

# Print the results
print(f'Control group averages for the last 10 trials:')
print(f'Hits: {control_averages[0]}')
print(f'False Alarms: {control_averages[1]}')
print(f'Correct Rejections: {control_averages[2]}')
print(f'Misses: {control_averages[3]}')

print(f'\nExperimental group averages for the last 10 trials:')
print(f'Hits: {experimental_averages[0]}')
print(f'False Alarms: {experimental_averages[1]}')
print(f'Correct Rejections: {experimental_averages[2]}')
print(f'Misses: {experimental_averages[3]}')

# Perform t-tests
t_test_hits = stats.ttest_ind(control_averages[0], experimental_averages[0])
t_test_fa = stats.ttest_ind(control_averages[1], experimental_averages[1])
t_test_cr = stats.ttest_ind(control_averages[2], experimental_averages[2])
t_test_misses = stats.ttest_ind(control_averages[3], experimental_averages[3])

print(f'T-test results for the last 10 trials:')
print(f'Hits: {t_test_hits}')
print(f'False Alarms: {t_test_fa}')
print(f'Correct Rejections: {t_test_cr}')
print(f'Misses: {t_test_misses}')
# %%
