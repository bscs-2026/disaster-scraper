def format_columns(df):
    return df.rename(columns={
        "text": "raw_text",
        "event_time_primary": "datetime",
        "location_matched_json": "location",
        "post_url": "url"
    })[
        [
            "source",
            "page_source",
            "text_content",
            "datetime",
            "location",
            "url",

        ]
    ]
