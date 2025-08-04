import pandas as pd

def load_and_standardize(path, source_label):
    # load
    df = pd.read_csv(path)

    # override all source entries
    df['source'] = source_label
    return df

def main():
    # load & standardize each dataset, with its fixed source label
    fb_df = load_and_standardize(
        'raw-data/fb_raw_disaster_posts.csv',
        source_label='Facebook'
    )
    x_df = load_and_standardize(
        'raw-data/x_raw_disaster_posts.csv',
        source_label='X'
    )

    # concatenate
    merged = pd.concat([fb_df, x_df], ignore_index=True)

    # quick sanity check
    print("Sources present:", merged['source'].unique())
    print(f"Total rows: {len(merged)}")

    # save
    merged.to_csv('raw-data/merged_raw_disaster_posts.csv', index=False)
    print("Wrote raw-data/merged_raw_disaster_posts.csv")

if __name__ == '__main__':
    main()
