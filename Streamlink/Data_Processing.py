import pandas as pd

# Load the uploaded JSON file into a DataFrame
df = pd.read_json(r"Data/Metrics.json")

df.head()  # Display the first few rows of the DataFrame
