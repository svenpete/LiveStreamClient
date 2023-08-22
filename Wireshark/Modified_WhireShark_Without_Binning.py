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

    # Calculate throughput for each time bin
    throughput_values = df_updated.groupby(pd.cut(df_updated["Time"], bins=time_bins))["Length"].sum() / time_interval

    # Plot throughput over time
    plt.figure(figsize=(14, 5))
    throughput_values.plot(label="Durchsatz (Bytes/s) " + protocol, color='blue')
    plt.title("Durchsatz über die Zeit")
    plt.xlabel("Zeit (s)")
    plt.ylabel("Durchsatz (Bytes/s)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(range(0, 121, 1))
    plt.plot()
    plt.savefig(os.path.join(directory_name, protocol + '_Durchsatz.png'))

    # Count retransmissions for each time bin
    retransmission_counts = df_updated[df_updated["Info"].str.contains("retransmission", case=False) |
                                       df_updated["Info"].str.contains("fast retransmission", case=False) |
                                       df_updated["Info"].str.contains("spurious retransmission", case=False)]
    retransmission_values = retransmission_counts.groupby(pd.cut(retransmission_counts["Time"], bins=time_bins)).size()

    # Plot packet loss (retransmissions) over time
    plt.figure(figsize=(14, 5))
    retransmission_values.plot(label="TCP-Neuübertragungen", color='red')
    plt.title("Paketverlust (TCP-Neuübertragungen) über die Zeit " + protocol)
    plt.xlabel("Zeit (s)")
    plt.ylabel("Anzahl der Neuübertragungen")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(range(0, 121, 1))
    plt.plot()
    plt.savefig(os.path.join(directory_name, protocol + '_PackageLoss.png'))

    # Calculate jitter values for each packet
    jitter_values_per_packet = df_updated["Time"].diff().abs()

    # Assign jitter values to dataframe
    df_updated["Jitter"] = jitter_values_per_packet

    # Calculate average jitter for each time bin
    average_jitter_values = df_updated.groupby(pd.cut(df_updated["Time"], bins=time_bins))["Jitter"].mean()

    # Plot jitter over time
    plt.figure(figsize=(14, 5))
    average_jitter_values.plot(label="Durchschnittlicher Jitter (s) " + protocol, color='green')
    plt.title("Jitter über die Zeit")
    plt.xlabel("Zeit (s)")
    plt.ylabel("Durchschnittlicher Jitter (s)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(range(0, 121, 1))

    plt.savefig(os.path.join(directory_name, protocol+'_Jitter.png'))
