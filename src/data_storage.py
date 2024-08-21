import pandas as pd


class Data_Storage:
    
    def __init__(self):
        pass
    
    def upload_files(self, filepath):  # Better word is import files
        df = pd.DataFrame()  # Create an empty dataframe
        try:
            
            extension = filepath.split(".")[-1].lower()

            if extension == "csv":
                df = pd.read_csv(filepath, delimiter=',')  # Use comma for CSV
            elif extension == "txt":
                df = pd.read_csv(filepath, delimiter='\t')  # Use tab for TXT
            else:
                raise ValueError(f"Unsupported file extension: {extension}")
        except  FileNotFoundError:
            print("Error: File not found at", filepath)        

        return df
        
    def save_csv(self,data,filepath):
        try:
            if isinstance(data, (dict, list)):
                data = pd.json_normalize(data)
            data.to_csv(filepath, index=False)
        except FileNotFoundError:
            print("Error: File not found at", filepath)
            return None    
        
    def save_json(self,data,json_output_path):
        try:
            with open(json_output_path , 'w') as f:
                f.write(data.text)
            print(f"Data saved successfully to {json_output_path}")
        except FileNotFoundError:
            print("Error: File not found at", json_output_path)
            return None   
        
    def save_excel(self, data, filepath):
        try:
            with pd.ExcelWriter(filepath) as writer:
                for sheet_name, df in data.items():
                    sheet = writer.book.create_sheet(sheet_name)
                    for row in dataframe_to_rows(group, index=False, header=True):
                        sheet.append(row)
                    # Make the first sheet visible to avoid the IndexError
                    if writer.book.active is None:
                        writer.book.active = len(writer.book.worksheets) - 1

        except FileNotFoundError:
            print(f"Error: File not found at {filepath}")