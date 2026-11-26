import pandas as pd

def convert_excel_file(input_excel_path, output_path, output_format):
    """
    Convert an Excel file to CSV or JSONL format.

    Args:
        input_excel_path (str): Path to the input Excel file.
        output_path (str): Path to save the converted file.
        output_format (str): 'csv' or 'jsonl'.
    """
    df = pd.read_excel(input_excel_path)

    if output_format.lower() == 'csv':
        df.to_csv(output_path, index=False)
    elif output_format.lower() == 'jsonl':
        # Convert datetime columns to string
        for col in df.select_dtypes(include=["datetime", "datetimetz"]).columns:
            df[col] = df[col].astype(str)
        df.to_json(output_path, orient="records", lines=True)
    else:
        raise ValueError("output_format must be 'csv' or 'jsonl'")


