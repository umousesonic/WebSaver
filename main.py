import requests
from bs4 import BeautifulSoup
import os
import sys
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import threading
from urllib.parse import urlparse
import re
import logging


logger = logging.getLogger();
logger.setLevel(logging.INFO)

def download_files(url):
    # Send a GET request to the URL
    try:
        response = requests.get(url)
    except Exception:
        return

    # Use the urlparse library to parse the URL and extract the first part of it
    parsed_url = urlparse(url)
    input_netloc = parsed_url.netloc
    input_scheme = parsed_url.scheme
    input_path = parsed_url.path

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all the links on the webpage
    links = soup.find_all("a")

    # Create a directory to store the downloaded files
    if not os.path.exists("downloaded_files"):
        os.makedirs("downloaded_files")

    # Loop through all the links and download the files
    for i, link in enumerate(links):
        href = link.get("href")

        if href:
            parsed_href = urlparse(href)
            if parsed_href.scheme and parsed_href.netloc:
                # href is a valid URL
                pass
            else:
                # href is not a valid URL
                if not parsed_href.scheme:
                    parsed_href = parsed_href._replace(scheme=input_scheme)
                if not parsed_href.netloc:
                    if (href[0] == '/'):
                        parsed_href = parsed_href._replace(netloc=input_netloc)
                    else:
                        parsed_href = parsed_href._replace(netloc=input_netloc, path=input_path+href)
                href = parsed_href.geturl()
            # Check for only http or https
            parsed_new_href = urlparse(href)
            href = str(href)
            if parsed_new_href.scheme != 'http' and parsed_new_href.scheme != 'https':
                logger.debug("Not valid: " + href)
                continue;

            logger.debug("sending request to: " + href)
            # Set the headers to include User-Agent of Mozilla Firefox
            # Get a copy of the default headers that requests would use
            headers = requests.utils.default_headers()

            # Update the headers with your custom ones
            headers.update(
                {
                    'User-Agent': 'Mozilla/5.0',
                }
            )

            # Send a HEAD request to the file URL to get the Content-Type header
            try:
                file_response = requests.head(href, headers=headers, allow_redirects=True)
                logger.debug("File Response: " + str(file_response))
            except Exception as e:
                logger.warning(e)
                continue


            content_type = file_response.headers.get('Content-Type')
            content_disposition = file_response.headers.get('Content-Disposition')

            if (content_type and 'application' in content_type) or (content_disposition and 'attachment' in content_disposition):
                logger.info("Getting file: " + href)
                # Send a GET request to the file URL
                try:
                    file_response = requests.get(href, stream=True)
                except Exception:
                    continue
                # # Write the file content to a file
                # filename = href.split("/")[-1]

                filename = ''
                if "Content-Disposition" in file_response.headers.keys():
                    filename = re.findall("filename=(.+)", file_response.headers["Content-Disposition"])
                    if filename:
                        filename = filename[0]
                    else:
                        filename = href.split("/")[-1]
                else:
                    filename = href.split("/")[-1]

                # Remove any character that the file system does not allow in filename from string variable filename
                filename = re.sub(r'[^\w\-_. ]', '', filename)

                with open(os.path.join(".", "downloaded_files", filename), "wb") as f:
                    total_length = file_response.headers.get('content-length')
                    if total_length is None: # no content length header
                        f.write(file_response.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for data in file_response.iter_content(chunk_size=4096):
                            dl += len(data)
                            f.write(data)
                            done = int(50 * dl / total_length)
                            progress_bar['value'] = done*2
                            file_label.config(text=f"Downloading {filename}...")
                            root.update_idletasks()

    file_label.config(text="Done!!")
    logger.info("Done.")

def get_url():
    url = url_entry.get()
    # Check for proper schema
    if not url.startswith('http') and not url.startswith('https'):
        url = 'http://' + url

    # Create a new thread to download files
    download_thread = threading.Thread(target=download_files,args=(url,))
    download_thread.start()

def browse_folder():
    folder_path = filedialog.askdirectory()
    os.chdir(folder_path)

root = tk.Tk()
root.title("File Downloader")

# Set the default size of the GUI
root.geometry("500x300")

# Create a frame to hold the widgets
frame = tk.Frame(root)
frame.pack(fill='both')

url_label = tk.Label(frame, text="Enter the URL to be scraped:", font=("Arial", 14))
url_label.pack(pady=10) 

url_entry = tk.Entry(frame, font=("Arial", 14))
url_entry.pack(fill='x', padx=10, pady=10) # Make url_entry the same width as the window

download_button = tk.Button(frame, text="Download Files", font=("Arial", 14), command=get_url, bg="pink", fg="white")
download_button.pack(pady=10)

file_label = tk.Label(frame, text="", font=("Arial", 14))
file_label.pack(pady=10)

progress_bar = ttk.Progressbar(frame, mode='determinate', style="pink.Horizontal.TProgressbar")
progress_bar.pack(fill='x', padx=10, pady=10)

# Configure the grid layout to be scalable
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)
frame.grid_columnconfigure(0, weight=1)
frame.grid_rowconfigure(0, weight=1)

style = ttk.Style()
style.theme_use("clam")
style.configure("pink.Horizontal.TProgressbar", foreground='pink', background='pink')

root.mainloop()
