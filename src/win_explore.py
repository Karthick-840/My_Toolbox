def sort_and_rename_files(self,rename=False):
    # Get all files in the folder and sort them alphabetically
        files = sorted([f for f in os.listdir(self.input_path) if os.path.isfile(os.path.join(self.input_path, f))])

        if rename:
        # Iterate over sorted files and rename them
            for index, filename in enumerate(files):
                file_extension = os.path.splitext(filename)[1]
                new_filename = f"{index + 1:04d}_{filename}"
                old_path = os.path.join(folder_path, filename)
                new_path = os.path.join(folder_path, new_filename)
                os.rename(old_path, new_path)
                print(f"Renamed '{filename}' to '{new_filename}'")
                
                
def combine_pdfs(self, output_filename, pdf_order):
            # Ensure the output folder exists
            os.makedirs(output_folder, exist_ok=True)
            
            for output_filename, file_sequence in pdf_order.items():
                writer = PdfWriter()
                
                for prefix in file_sequence:
                    prefix_str = f"{prefix:04d}_"
                    print(prefix_str)
                    # Find the file that starts with the current prefix
                    input_filename = next((f for f in os.listdir(self.input_path) if f.startswith(prefix_str)), None)
                    if input_filename:
                        input_path = os.path.join(self.input_path, input_filename)
                        reader = PdfReader(input_path)
                        for page_num in range(len(reader.pages)):
                            writer.add_page(reader.pages[page_num])
                    else:
                        print(f"File not found for prefix: {prefix_str}")
                
                output_path = os.path.join(self.output_path, f"{output_filename}.pdf")
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
                print(f"Created {output_filename}.pdf")