# YouTube Video Screenshot to PDF

This Streamlit app downloads one or more YouTube videos, captures distinct full-resolution screenshots from each video, and exports each video into its own landscape PDF file.

The app does not use OCR, does not require Tesseract, and does not create PowerPoint files.

## Features

- Process multiple YouTube links sequentially.
- Show the current processing stage for each video.
- Show each completed video's result immediately, without waiting for the full batch to finish.
- Export one PDF per video.
- Use the YouTube video title as the PDF filename.
- Convert filenames to lowercase ASCII slugs with hyphens, for example `my-video-title.pdf`.
- Keep screenshots in the same order they appear in the video.
- Keep images at their original video resolution.
- Preserve image aspect ratio in a landscape PDF page.
- Hide slide previews by default; expand a video result to preview all pages.

## Requirements

- A computer with Windows, macOS, or Linux.
- Python 3.10 or newer.
- Internet access.
- A browser.
- The project files in this folder.

## Install Python

Skip this section if Python is already installed.

### Windows

1. Go to <https://www.python.org/downloads/>.
2. Download the latest stable Python 3 installer.
3. Run the installer.
4. Important: check **Add python.exe to PATH** on the first installer screen.
5. Click **Install Now**.
6. Open PowerShell and verify:

```powershell
py --version
```

You should see a Python version such as `Python 3.12.x`.

### macOS

Option 1: install from Python.org:

1. Go to <https://www.python.org/downloads/>.
2. Download the latest stable Python 3 macOS installer.
3. Run the `.pkg` installer.
4. Open Terminal and verify:

```bash
python3 --version
```

Option 2: install with Homebrew:

```bash
brew install python
python3 --version
```

### Ubuntu or Debian Linux

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 --version
```

## Get the Project

If you have Git installed:

```bash
git clone <your-repository-url>
cd youtube-slide-extractor
```

If you do not have Git:

1. Download the project as a ZIP file.
2. Extract it.
3. Open a terminal in the extracted folder.

The folder should contain at least:

```text
app.py
requirements.txt
README.md
```

## Create a Virtual Environment

A virtual environment keeps this app's Python packages separate from the rest of your computer.

### Windows PowerShell

Run these commands inside the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run this once:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### macOS or Linux

Run these commands inside the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

When the environment is active, your terminal prompt usually starts with `(.venv)`.

## Run the App

Make sure the virtual environment is active, then run:

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually:

```text
http://localhost:8501
```

Open that URL in your browser.

## How to Use

1. Paste one or more YouTube URLs into the text box.
2. Put one URL per line.
3. Adjust **Capture interval in seconds** if needed.
4. Adjust **Consecutive duplicate merge strength** if needed.
5. Click **Create PDFs for all videos**.
6. Watch each video's status:
   - Queued
   - Downloading video
   - Capturing slides
   - Creating PDF
   - Ready
7. As soon as a video finishes, its result appears immediately.
8. Click **Download PDF** for that video.
9. Open **Preview all slides** if you want to inspect every PDF page before downloading.

## Settings

### Capture interval in seconds

This controls how often the app samples frames from the video.

- Lower value: captures more frames, catches quick slide changes, takes longer.
- Higher value: faster, smaller output, may miss very quick slide changes.

Good starting value: `1.0`.

### Consecutive duplicate merge strength

This controls how aggressively the app merges consecutive frames that look like the same slide.

- Lower value: keeps more pages.
- Higher value: merges more repeated pages.

Good starting value: `5`.

## Output Files

Each video gets its own PDF.

The PDF filename is based on the YouTube title:

```text
Original title: "My First Lecture: Introduction!"
PDF filename:  my-first-lecture-introduction.pdf
```

If two videos have the same title, the app adds a number:

```text
my-video.pdf
my-video-2.pdf
my-video-3.pdf
```

## Troubleshooting

### `python` or `py` is not recognized

Python is not installed, or it was installed without adding it to PATH.

Install Python again and make sure **Add python.exe to PATH** is checked on Windows.

### `streamlit` is not recognized

Activate the virtual environment first, then install dependencies again:

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### A YouTube video fails to download

Try updating `yt-dlp`:

```bash
python -m pip install --upgrade yt-dlp
```

Then run the app again:

```bash
streamlit run app.py
```

Some videos may still fail because of YouTube restrictions, private videos, age checks, region restrictions, or temporary network problems.

### The PDF has too many pages

Increase **Consecutive duplicate merge strength**.

You can also increase **Capture interval in seconds** to sample fewer frames.

### The PDF misses slides

Lower **Capture interval in seconds**.

For fast-changing videos, try `0.5` or `0.25`.

### Processing is slow

This is normal for long or high-resolution videos.

To make it faster:

- Increase **Capture interval in seconds**.
- Process fewer links at once.
- Close other heavy apps.

## Dependencies

The Python packages are listed in `requirements.txt`:

```text
streamlit
opencv-python
Pillow
imagehash
yt-dlp
```

## Project Structure

```text
youtube-slide-extractor/
  app.py
  requirements.txt
  README.md
```
