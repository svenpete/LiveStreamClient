# Reload the updated CSV file into a dataframe
import os
import datetime

import pandas as pd
csv_files = ['DMA_RTMP_CSV.csv', 'DMA_MPEG_DASH_CSV.csv', 'DMA_HLS_CSV.csv', 'DMA_RTSP_CSV.csv']
Protocol = ['RTMP', 'MPEG-DASH', 'HLS', 'RTSP']
for file_name, protocol in zip(csv_files, Protocol):
    df_updated = pd.read_csv("Data/csv/" + file_name)

    # Display the first few rows to understand its structure
    df_updated.head()

    # Calculate throughput

    # Total transmitted data in bytes
    total_data = df_updated["Length"].sum()

    # Total time duration
    time_duration = df_updated["Time"].max() - df_updated["Time"].min()

    # Throughput in bytes per second
    throughput = total_data / time_duration

    print(f"Throughput {throughput}")

    # Filter SYN packets
    syn_packets = df_updated[df_updated["Info"].str.contains("[SYN]") & ~df_updated["Info"].str.contains("[SYN, ACK]")]
    syn_packets = syn_packets.set_index('No.')

    # Filter SYN-ACK packets
    syn_ack_packets = df_updated[df_updated["Info"].str.contains("[SYN, ACK]")]
    syn_ack_packets = syn_ack_packets.set_index('No.')

    # Calculate RTT for each SYN/SYN-ACK pair
    rtts = []
    for idx, syn_pkt in syn_packets.iterrows():
        # Find corresponding SYN-ACK packet
        corresponding_syn_ack = syn_ack_packets[(syn_ack_packets['Source'] == syn_pkt['Destination']) &
                                                (syn_ack_packets['Destination'] == syn_pkt['Source']) &
                                                (syn_ack_packets['Time'] > syn_pkt['Time'])]
        if not corresponding_syn_ack.empty:
            syn_ack_pkt = corresponding_syn_ack.iloc[0]
            rtt = syn_ack_pkt['Time'] - syn_pkt['Time']
            rtts.append(rtt)

    # Calculate average RTT
    average_rtt = sum(rtts) / len(rtts) if rtts else 0

    print(f"Average RTT: {average_rtt}")

    # Filter retransmitted packets (based on common indications of retransmissions in Wireshark)
    retransmissions = df_updated[df_updated["Info"].str.contains("retransmission", case=False) |
                                 df_updated["Info"].str.contains("fast retransmission", case=False) |
                                 df_updated["Info"].str.contains("spurious retransmission", case=False)]

    # Calculate packet loss rate based on retransmissions
    # This is an estimate since retransmissions might not capture all lost packets
    packet_loss_rate = len(retransmissions) / len(df_updated) * 100

    print(f"Package Loss: {packet_loss_rate}")

    # Calculate differences in packet arrival times to get jitter values
    jitter_values = df_updated["Time"].diff().dropna().abs()

    # Calculate average jitter
    average_jitter = jitter_values.mean()

    print(f"Avg. Jitter: {average_jitter}")

    import matplotlib.pyplot as plt

    # Saving all figures
    current_time_str = datetime.datetime.now().strftime('Whireshark_%Y-%m-%d_%H-%M-%S')
    directory_name = f"Results_{current_time_str}_{protocol}"
    os.makedirs(directory_name, exist_ok=True)

    # Define a time interval for calculating metrics (e.g., 1 second)
    time_interval = 1.0

    # Create time bins for the entire duration
    time_bins = list(range(0, int(df_updated["Time"].max()) + 2, int(time_interval)))

    # Create a single figure and 3 subplots (horizontally)
    fig, axs = plt.subplots(nrows=1, ncols=3, figsize=(20, 5))

    # Plot 1: Throughput over time
    throughput_values = df_updated.groupby(pd.cut(df_updated["Time"], bins=time_bins))["Length"].sum() / time_interval
    throughput_values.index = throughput_values.index.map(lambda x: x.mid)

    print(throughput_values.head())

    axs[0].plot(throughput_values, label="Durchsatz (Bytes/s) " + protocol, color='blue')
    axs[0].set_title("Durchsatz über die Zeit")
    axs[0].set_xlabel("Zeit (s)")
    axs[0].set_ylabel("Durchsatz (Bytes/s)")
    axs[0].legend()
    axs[0].grid(True)

    # Plot 2: Packet loss (retransmissions) over time
    retransmission_counts = df_updated[df_updated["Info"].str.contains("retransmission", case=False) |
                                       df_updated["Info"].str.contains("fast retransmission", case=False) |
                                       df_updated["Info"].str.contains("spurious retransmission", case=False)]
    retransmission_values = retransmission_counts.groupby(pd.cut(retransmission_counts["Time"], bins=time_bins)).size()
    retransmission_values.index = retransmission_values.index.map(lambda x: x.mid)
    axs[1].plot(retransmission_values, label="TCP-Neuübertragungen", color='red')
    axs[1].set_title("Paketverlust (TCP-Neuübertragungen) über die Zeit " + protocol)
    axs[1].set_xlabel("Zeit (s)")
    axs[1].set_ylabel("Anzahl der Neuübertragungen")
    axs[1].legend()
    axs[1].grid(True)

    # Plot 3: Jitter over time
    jitter_values_per_packet = df_updated["Time"].diff().abs()
    df_updated["Jitter"] = jitter_values_per_packet
    average_jitter_values = df_updated.groupby(pd.cut(df_updated["Time"], bins=time_bins))["Jitter"].mean()
    average_jitter_values.index = average_jitter_values.index.map(lambda x: x.mid)
    axs[2].plot(average_jitter_values, label="Durchschnittlicher Jitter (s) " + protocol, color='green')
    axs[2].set_title("Jitter über die Zeit")
    axs[2].set_xlabel("Zeit (s)")
    axs[2].set_ylabel("Durchschnittlicher Jitter (s)")
    axs[2].legend()
    axs[2].grid(True)

    # Adjust layout
    plt.tight_layout()

    # Save the entire figure
    fig.savefig(os.path.join(directory_name, protocol + '_CombinedMetrics.png'))

    # Show the figure
    plt.show()
