Of course! Here’s the English version of your project description for GitHub:

---

## Image Downloader

**image\_downloader.py** is a Python script that automatically searches for and downloads images from Google based on a list of keywords. The script saves images in PNG format, with a filter for landscape orientation to ensure the right aspect ratio and quality. This tool is useful for building image datasets, research, or any machine learning project requiring high-quality images.

### Features

* **Automatic image search on Google** using Custom Search API.
* **Filters images by landscape aspect ratio** (width/height >= 1.3).
* **Stores downloaded image URLs** to avoid duplicates.
* **Saves images as PNG** with automatic numbering.
* **Supports multiple keywords** through a `keywords.txt` file.

### Usage

1. **Install required libraries:**

   ```bash
   pip install requests pillow
   ```

2. **Prepare the `keywords.txt` file** (one keyword per line).

3. **Configure your API Key and Search Engine ID** in the script if needed.

4. **Run the script:**

   ```bash
   python image_downloader.py
   ```

### Notes

* The script uses Google Custom Search API, so you need a valid API Key and Search Engine ID.
* Downloaded images are saved in the `images/` directory, and the list of downloaded URLs is stored in `downloaded_log.txt`.

### Contact

If you encounter any issues or would like to contribute, please create an issue or a pull request on this repository.

---

