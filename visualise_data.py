import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def main():
    # Load data
    df = pd.read_csv('simulation_results copy.csv')

    # Setup Seaborn
    sns.set(style='whitegrid')

    # Plot Histograms for MTTF and MTTR
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    sns.histplot(df['mttf'], kde=True, color='blue')
    plt.title('Histogram of Mean Time to Failure (MTTF)')
    plt.xlabel('MTTF')
    plt.ylabel('Frequency')

    plt.subplot(1, 2, 2)
    sns.histplot(df['mttr'], kde=True, color='red')
    plt.title('Histogram of Mean Time to Repair (MTTR)')
    plt.xlabel('MTTR')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.show()

    # Scatter Plot of MTTF vs MTTR
    sns.scatterplot(data=df, x='mttf', y='mttr', hue='(r,s)', style='(m,n)')
    plt.title('Scatter Plot of MTTF vs MTTR')
    plt.xlabel('Mean Time to Failure (MTTF)')
    plt.ylabel('Mean Time to Repair (MTTR)')
    plt.legend(title='Configurations', bbox_to_anchor=(1.05, 1), loc=2)
    plt.show()

    # Line Plot for First Fail and First Repair Times
    plt.figure(figsize=(12, 6))
    sns.lineplot(data=df, x='iteration', y='ff', marker='o', label='First Fail Time')
    sns.lineplot(data=df, x='iteration', y='fr', marker='o', label='First Repair Time')
    plt.title('First Fail and First Repair Times Over Iterations')
    plt.xlabel('Iteration')
    plt.ylabel('Time')
    plt.legend()
    plt.show()

    # Boxplot of Elapsed Time by Configuration
    df['configurations'] = df['(m,n)'].astype(str) + ', ' + df['(r,s)'].astype(str)
    sns.boxplot(data=df, x='configurations', y='elapsed_time')
    plt.xticks(rotation=45)
    plt.title('Boxplot of Elapsed Time for Different Configurations')
    plt.xlabel('Configurations (m,n), (r,s)')
    plt.ylabel('Elapsed Time (seconds)')
    plt.show()

    # Heatmap of MTTF and MTTR for Different Configurations
    pivot_table_mttf = df.pivot_table(index='(m,n)', columns='(r,s)', values='mttf', aggfunc=np.mean)
    pivot_table_mttr = df.pivot_table(index='(m,n)', columns='(r,s)', values='mttr', aggfunc=np.mean)
    plt.figure(figsize=(12, 10))
    plt.subplot(1, 2, 1)
    sns.heatmap(pivot_table_mttf, annot=True, cmap='Blues', fmt=".2f")
    plt.title('Average MTTF for Different Configurations')
    plt.xlabel('(r,s)')
    plt.ylabel('(m,n)')

    plt.subplot(1, 2, 2)
    sns.heatmap(pivot_table_mttr, annot=True, cmap='Reds', fmt=".2f")
    plt.title('Average MTTR for Different Configurations')
    plt.xlabel('(r,s)')
    plt.ylabel('(m,n)')
    plt.tight_layout()
    plt.show()

    # Bar Graph of Failures and Repairs per Simulation Time
    df_agg = df.groupby('sim_time').agg({'ff': 'count', 'fr': 'count'}).reset_index()
    df_agg.rename(columns={'ff': 'Number of Failures', 'fr': 'Number of Repairs'}, inplace=True)
    df_agg.plot(x='sim_time', kind='bar', stacked=True)
    plt.title('Number of Failures and Repairs per Simulation Time')
    plt.xlabel('Simulation Time')
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    plt.show()

if __name__ == "__main__":
    main()
