import pandas as pd

df = pd.read_csv("spotify_songs.csv")

sizes = [1000, 2000, 4000, 8000, 16000, 32000, 64000]

for n in sizes:
    df.head(n).to_csv(f"spotify_{n}.csv", index=False)
