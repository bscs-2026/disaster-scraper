def format_columns(df):
    return df.rename(columns={
        "text": "raw_text",
        "text_content": "text_content",
        # "date-time": "date-time",
        "post_url": "url"
    })[
        # ["source","extracted_date_time", "date-time", "text_content", "url"]
        ["source", "page_source", "text_content", "url"]

    ]
