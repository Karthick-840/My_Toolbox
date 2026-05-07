import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os

class ImageViewer:
    """
    A simple image viewer application built with Tkinter.
    Allows browsing images in a directory using arrow keys.
    """
    def __init__(self, master):
        self.master = master
        master.title("Python Image Viewer")
        master.geometry("800x600") # Set initial window size
        master.configure(bg="#2c3e50") # Dark background for the window

        self.image_files = []
        self.current_image_index = -1
        self.image_dir = ""

        # --- GUI Elements ---

        # Frame for controls (buttons)
        self.control_frame = tk.Frame(master, bg="#34495e", pady=10)
        self.control_frame.pack(side=tk.TOP, fill=tk.X)

        # "Open Folder" Button
        self.open_button = tk.Button(
            self.control_frame,
            text="Open Folder",
            command=self.open_folder,
            bg="#2ecc71", # Emerald green
            fg="white",
            font=("Inter", 12, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8,
            activebackground="#27ae60",
            activeforeground="white"
        )
        self.open_button.pack(side=tk.LEFT, padx=10)

        # Label to display current directory (optional, but helpful)
        self.dir_label = tk.Label(
            self.control_frame,
            text="No folder selected",
            bg="#34495e",
            fg="#ecf0f1", # Light gray
            font=("Inter", 10)
        )
        self.dir_label.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        # Frame for image display
        self.image_frame = tk.Frame(master, bg="#34495e", bd=5, relief=tk.GROOVE)
        self.image_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Label to display the image
        self.image_label = tk.Label(self.image_frame, bg="#34495e")
        self.image_label.pack(expand=True)

        # Label to display image filename
        self.filename_label = tk.Label(
            master,
            text="No image loaded",
            bg="#2c3e50",
            fg="#bdc3c7", # Muted gray
            font=("Inter", 10, "italic"),
            pady=5
        )
        self.filename_label.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Key Bindings ---
        master.bind("<Left>", self.show_previous_image)
        master.bind("<Right>", self.show_next_image)
        master.bind("<Configure>", self.on_window_resize) # Bind to window resize event

    def open_folder(self):
        """
        Opens a directory dialog, loads image files, and displays the first image.
        """
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.image_dir = folder_selected
            self.dir_label.config(text=f"Folder: {os.path.basename(self.image_dir)}")
            self.load_images_from_folder()

    def load_images_from_folder(self):
        """
        Loads all common image files from the selected directory.
        """
        self.image_files = []
        supported_formats = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp")
        
        # Get list of files and sort them for consistent order
        for f in sorted(os.listdir(self.image_dir)):
            if f.lower().endswith(supported_formats):
                self.image_files.append(os.path.join(self.image_dir, f))

        if not self.image_files:
            messagebox.showinfo("No Images", "No supported image files found in the selected folder.")
            self.current_image_index = -1
            self.image_label.config(image=None)
            self.filename_label.config(text="No image loaded")
            return

        self.current_image_index = 0
        self.display_image()

    def display_image(self):
        """
        Displays the image at the current_image_index.
        Resizes the image to fit the image_frame.
        """
        if not self.image_files:
            return

        image_path = self.image_files[self.current_image_index]
        try:
            pil_image = Image.open(image_path)
            
            # Get current size of the image frame
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()

            # Ensure frame has a non-zero size before resizing
            if frame_width == 1 or frame_height == 1: # Default Tkinter size if not yet rendered
                # Use a sensible default or current window size if frame isn't fully rendered
                frame_width = self.master.winfo_width() - 40 # Account for padding
                frame_height = self.master.winfo_height() - self.control_frame.winfo_height() - self.filename_label.winfo_height() - 40 # Account for padding and other elements
                frame_width = max(frame_width, 100) # Minimum size
                frame_height = max(frame_height, 100) # Minimum size


            # Calculate new size while maintaining aspect ratio
            img_width, img_height = pil_image.size
            
            # Prevent division by zero if frame dimensions are zero
            if frame_width <= 0: frame_width = 1
            if frame_height <= 0: frame_height = 1

            aspect_ratio = img_width / img_height

            if img_width > frame_width or img_height > frame_height:
                if (frame_width / aspect_ratio) <= frame_height:
                    new_width = frame_width
                    new_height = int(frame_width / aspect_ratio)
                else:
                    new_height = frame_height
                    new_width = int(frame_height * aspect_ratio)
                
                # Ensure new_width and new_height are at least 1
                new_width = max(1, new_width)
                new_height = max(1, new_height)

                pil_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert PIL image to Tkinter PhotoImage
            self.tk_image = ImageTk.PhotoImage(pil_image)
            self.image_label.config(image=self.tk_image)
            self.filename_label.config(text=os.path.basename(image_path))

        except Exception as e:
            messagebox.showerror("Error", f"Could not load image {os.path.basename(image_path)}: {e}")
            self.image_label.config(image=None)
            self.filename_label.config(text="Error loading image")

    def show_next_image(self, event=None):
        """
        Navigates to and displays the next image in the list.
        """
        if self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.display_image()

    def show_previous_image(self, event=None):
        """
        Navigates to and displays the previous image in the list.
        """
        if self.image_files:
            self.current_image_index = (self.current_image_index - 1 + len(self.image_files)) % len(self.image_files)
            self.display_image()
            
    def on_window_resize(self, event):
        """
        Called when the window is resized. Re-displays the current image to fit.
        """
        # Ensure we only process resize events for the root window or image_frame
        # to avoid excessive calls from internal widget resizes.
        if event.widget == self.master or event.widget == self.image_frame:
            # Only re-display if there are images and if the image frame has actual dimensions
            if self.image_files and self.image_frame.winfo_width() > 1 and self.image_frame.winfo_height() > 1:
                self.display_image()


# --- Main Application Loop ---
if __name__ == "__main__":
    # To run this code, you need to install Pillow (PIL) library:
    # pip install Pillow

    root = tk.Tk()
    app = ImageViewer(root)
    root.mainloop()



# Threading Vs MultiProcessing in Python

# Python is multithreaded but not simulateanously multi threaded

# Process is a one instance of a program. it has code and data and meoery set aside for each. . A process has atleast one thread. the sysmte allocates registry and stack for that one thread. smallest sequence of isntance to determine when and how long fo proces to run. it has access to code and data. 
#a new process will have its own set of code and data and has its own tread withr eigstry and stack allocated. one process wont ahve acess to another processes data. to do some they need quees and pipes.
# Multi threading is doog multiple processes at same time


# This is running things synchronously. So thats why you see time taken for same process at two intervals. her eis where you get to see the importnace of threading and concurancy. understand diff between CPU bound tasks (crunching numbers) and I/O tasks (waiting for input and output ops)

# when tasks are about wiating, this will take time so we can make I/O tasks run concurrently. it doesnt runs eaclty run concurlyt, it creates a illusion. it starts s funciton and continues and executes the second until the next one gets sdone. 

# Thread Pull executor

import requests
import time
import concurrent.futures

img_urls = [
    'https://images.unsplash.com/photo-1516117172878-fd2c41f4a759',
    'https://images.unsplash.com/photo-1532009324734-20a7a5813719',
    'https://images.unsplash.com/photo-1524429656589-6633a470097c',
    'https://images.unsplash.com/photo-1530224264768-7ff8c1789d79',
    'https://images.unsplash.com/photo-1564135624576-c5c88640f235',
    'https://images.unsplash.com/photo-1541698444083-023c97d3f4b6',
    'https://images.unsplash.com/photo-1522364723953-452d3431c267',
    'https://images.unsplash.com/photo-1513938709626-033611b8cc03',
    'https://images.unsplash.com/photo-1507143550189-fed454f93097',
    'https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e',
    'https://images.unsplash.com/photo-1504198453319-5ce911bafcde',
    'https://images.unsplash.com/photo-1530122037265-a5f1f91d3b99',
    'https://images.unsplash.com/photo-1516972810927-80185027ca84',
    'https://images.unsplash.com/photo-1550439062-609e1531270e',
    'https://images.unsplash.com/photo-1549692520-acc6669e2f0c'
]

t1 = time.perf_counter()

for img_url in img_urls:
    img_bytes = requests.get(img_url).content
    img_name = img_url.split('/')[3]
    img_name = f'{img_name}.jpg'
    with open(img_name, 'wb') as img_file:
        img_file.write(img_bytes)
        print(f'{img_name} was downloaded...')



t2 = time.perf_counter()

print(f'\nFinished in {t2-t1} seconds\n')

t1 = time.perf_counter()



def download_image(img_url):
    img_bytes = requests.get(img_url).content
    img_name = img_url.split('/')[3]
    img_name = f'{img_name}.jpg'
    with open(img_name, 'wb') as img_file:
        img_file.write(img_bytes)
        print(f'{img_name} was downloaded...')


with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(download_image, img_urls)


t2 = time.perf_counter()

print(f'Finished in {t2-t1} seconds')

import cv2
import numpy as np
from rembg import remove
from PIL import Image

def extract_signature(image_path, output_path='signature.png'):
    # Load image and remove background
    with open(image_path, 'rb') as f:
        no_bg = remove(f.read())

    # Convert to OpenCV format
    image = Image.open(BytesIO(no_bg)).convert("RGBA")
    cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGRA)

    # Convert to grayscale & threshold to isolate signature
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours and extract largest one (likely the signature)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No signature found.")
        return

    # Get bounding box of the signature
    x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
    signature = cv_image[y:y+h, x:x+w]

    # Save extracted signature
    cv2.imwrite(output_path, signature)
    print(f"Signature saved to {output_path}")

# Example usage
from io import BytesIO
extract_signature("WhatsApp Image 2025-07-28 at 09.46.36.jpeg")
