import io
import os
import re
import tempfile
import unicodedata
from pathlib import Path

import cv2
import imagehash
import streamlit as st
import yt_dlp as youtube_dl
from PIL import Image, ImageOps


PDF_DPI = 300
PDF_QUALITY = 95
RESAMPLING_FILTER = getattr(Image, "Resampling", Image).LANCZOS
SIGNATURE_SIZE = (160, 90)
PIXEL_DIFFERENCE_THRESHOLD = 3.0
CHANGED_AREA_THRESHOLD = 0.01
DEFAULT_CAPTURE_INTERVAL_SECONDS = 0.5
DEFAULT_DUPLICATE_MERGE_STRENGTH = 3


def apply_page_style():
    st.markdown(
        """
        <style>
        :root {
            --surface: rgba(255, 255, 255, 0.88);
            --surface-strong: #ffffff;
            --text: #0f172a;
            --muted: #64748b;
            --blue: #2563eb;
            --cyan: #0891b2;
            --amber: #f59e0b;
            --green: #0f766e;
            --border: rgba(15, 23, 42, 0.10);
        }

        .stApp {
            background: linear-gradient(135deg, #f8fbff 0%, #ffffff 48%, #fff7ed 100%);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: rgba(248, 250, 252, 0.76);
            backdrop-filter: blur(10px);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .app-hero {
            color: white;
            border-radius: 8px;
            padding: 28px 30px;
            margin-bottom: 20px;
            background:
                linear-gradient(120deg, rgba(37, 99, 235, 0.97), rgba(8, 145, 178, 0.91) 56%, rgba(245, 158, 11, 0.86));
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.24);
        }

        .hero-eyebrow {
            margin: 0 0 8px;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
            opacity: 0.86;
        }

        .app-hero h1 {
            margin: 0;
            max-width: 760px;
            font-size: clamp(2.2rem, 5vw, 3.5rem);
            line-height: 1.04;
            letter-spacing: 0;
        }

        .app-hero p {
            margin: 14px 0 0;
            max-width: 720px;
            font-size: 1.03rem;
            line-height: 1.55;
            color: rgba(255, 255, 255, 0.91);
        }

        .hero-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin-top: 20px;
        }

        .hero-stat {
            border-radius: 8px;
            padding: 12px 14px;
            border: 1px solid rgba(255, 255, 255, 0.25);
            background: rgba(255, 255, 255, 0.14);
        }

        .hero-stat strong {
            display: block;
            font-size: 1.04rem;
            line-height: 1.25;
        }

        .hero-stat span {
            display: block;
            margin-top: 2px;
            font-size: 0.82rem;
            color: rgba(255, 255, 255, 0.82);
        }

        .section-kicker {
            margin: 0 0 0.5rem;
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #0f172a;
            background: #e0f2fe;
            border: 1px solid rgba(8, 145, 178, 0.20);
            border-radius: 999px;
            padding: 6px 10px;
            font-weight: 700;
            font-size: 0.88rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: var(--blue);
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.14);
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--surface);
            border-color: var(--border);
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.07);
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="slider"] {
            border-radius: 8px;
        }

        .stButton > button,
        .stDownloadButton > button {
            border-radius: 8px;
            border: 0;
            font-weight: 700;
            min-height: 2.8rem;
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.20);
        }

        .stButton > button {
            color: white;
            background: linear-gradient(90deg, var(--blue), var(--cyan));
        }

        .stDownloadButton > button {
            color: white;
            background: linear-gradient(90deg, var(--green), var(--cyan));
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            color: white;
            border: 0;
            filter: brightness(0.98);
        }

        [data-testid="stProgress"] > div > div > div > div {
            background: linear-gradient(90deg, var(--blue), var(--cyan), var(--amber));
        }

        [data-testid="stMetric"] {
            background: rgba(37, 99, 235, 0.06);
            border: 1px solid rgba(37, 99, 235, 0.10);
            border-radius: 8px;
            padding: 12px 14px;
        }

        @media (max-width: 760px) {
            .block-container {
                padding-top: 1rem;
            }

            .app-hero {
                padding: 22px 18px;
            }

            .hero-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <div class="app-hero">
            <p class="hero-eyebrow">Batch PDF builder</p>
            <h1>YouTube Slides to PDF</h1>
            <p>Capture sharp video frames in order and export one clean landscape PDF per video.</p>
            <div class="hero-grid">
                <div class="hero-stat"><strong>0.5s default</strong><span>More chances to catch fast slide changes</span></div>
                <div class="hero-stat"><strong>Merge strength 3</strong><span>Stricter duplicate detection by default</span></div>
                <div class="hero-stat"><strong>Per-video results</strong><span>Preview and download as each video finishes</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def slugify_filename(value, fallback="youtube-video"):
    normalized = unicodedata.normalize("NFKD", (value or "").replace("đ", "d").replace("Đ", "D"))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    slug = re.sub(r"-{2,}", "-", slug)
    slug = slug[:120].rstrip("-")
    return slug or fallback


def make_unique_slug(slug, used_slugs):
    if slug not in used_slugs:
        used_slugs.add(slug)
        return slug

    counter = 2
    while f"{slug}-{counter}" in used_slugs:
        counter += 1

    unique_slug = f"{slug}-{counter}"
    used_slugs.add(unique_slug)
    return unique_slug


def parse_youtube_urls(raw_urls):
    return [line.strip() for line in raw_urls.splitlines() if line.strip()]


def download_video(url, output_dir):
    """Download the highest-quality video stream that OpenCV can read later."""
    output_template = os.path.join(output_dir, "video.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]/bestvideo/best[ext=mp4]/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "no_progress": True,
    }

    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            prepared_filename = ydl.prepare_filename(info)
            video_title = info.get("title") or "youtube-video"

        if os.path.exists(prepared_filename):
            return prepared_filename, video_title

        downloaded_files = [path for path in Path(output_dir).iterdir() if path.is_file()]
        if downloaded_files:
            return str(max(downloaded_files, key=lambda path: path.stat().st_size)), video_title

        return None
    except Exception as exc:
        print(f"Error: {exc}")
        return None


def process_youtube_video(
    url,
    video_dir,
    capture_interval_seconds,
    hash_threshold,
    stage_callback=None,
):
    def set_stage(stage, detail=None):
        if stage_callback:
            stage_callback(stage, detail)

    set_stage("Downloading video", "Fetching the highest-quality readable video stream.")
    download_result = download_video(url, video_dir)
    if not download_result:
        raise RuntimeError("Could not download the video. Check the URL and try again.")

    video_path, video_title = download_result
    set_stage("Capturing slides", video_title)
    screenshots = extract_unique_screenshots(
        video_path,
        capture_interval_seconds=capture_interval_seconds,
        hash_threshold=hash_threshold,
    )

    if not screenshots:
        raise RuntimeError("No screenshots were found in this video.")

    set_stage("Creating PDF", f"{len(screenshots)} pages detected.")
    pdf_bytes = create_pdf_bytes(screenshots)
    set_stage("Ready", f"{len(screenshots)} pages.")
    return {
        "title": video_title,
        "screenshots": screenshots,
        "page_count": len(screenshots),
        "pdf_bytes": pdf_bytes,
    }


def render_video_result(result):
    if result.get("error"):
        st.subheader(f"Video {result['index']}/{result['total']}")
        st.caption(result["url"])
        st.error(result["error"])
        return

    title_column, action_column = st.columns([3, 1], gap="large")

    with title_column:
        st.subheader(f"{result['index']}. {result['title']}")
        st.caption(result["url"])
        st.success("Ready")
        st.caption(f"File name: {result['file_slug']}.pdf")

    with action_column:
        st.metric("Pages", result["page_count"])
        st.download_button(
            "Download PDF",
            data=result["pdf_bytes"],
            file_name=f"{result['file_slug']}.pdf",
            mime="application/pdf",
            key=f"download-{result['file_slug']}",
            on_click="ignore",
            use_container_width=True,
        )

    with st.expander("Preview all slides", expanded=False):
        for index, screenshot in enumerate(result["screenshots"], start=1):
            st.image(
                screenshot,
                caption=f"Page {index}",
                width="stretch",
            )


def render_video_status(slot, index, total, url, stage, detail=None):
    slot.empty()
    with slot.container(border=True):
        st.subheader(f"Video {index}/{total}")
        st.caption(url)
        st.markdown(
            f'<div class="status-pill"><span class="status-dot"></span>{stage}</div>',
            unsafe_allow_html=True,
        )
        if detail:
            st.caption(detail)


def render_video_result_slot(slot, result):
    slot.empty()
    with slot.container(border=True):
        render_video_result(result)


def frame_sharpness(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def frame_signature(frame):
    return cv2.resize(frame, SIGNATURE_SIZE, interpolation=cv2.INTER_AREA)


def is_same_consecutive_slide(hash_value, signature, current_entry, hash_threshold):
    hash_distance = abs(hash_value - current_entry["hash"])
    if hash_distance > hash_threshold:
        return False

    diff = cv2.absdiff(signature, current_entry["signature"])
    mean_difference = diff.mean()
    changed_area = (diff.max(axis=2) > 18).mean()

    return (
        mean_difference <= PIXEL_DIFFERENCE_THRESHOLD
        and changed_area <= CHANGED_AREA_THRESHOLD
    )


def make_slide_entry(hash_value, image, sharpness, signature):
    return {
        "hash": hash_value,
        "image": image.copy(),
        "sharpness": sharpness,
        "signature": signature,
    }


def extract_unique_screenshots(
    video_path,
    capture_interval_seconds=DEFAULT_CAPTURE_INTERVAL_SECONDS,
    hash_threshold=DEFAULT_DUPLICATE_MERGE_STRENGTH,
):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Could not open the downloaded video file.")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_interval = max(int(round(fps * capture_interval_seconds)), 1)
    frame_id = 0
    slide_entries = []
    current_entry = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % frame_interval == 0:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(rgb_frame)
            hash_value = imagehash.phash(image)
            sharpness = frame_sharpness(frame)
            signature = frame_signature(frame)

            if current_entry is None:
                current_entry = make_slide_entry(hash_value, image, sharpness, signature)
            elif is_same_consecutive_slide(
                hash_value,
                signature,
                current_entry,
                hash_threshold,
            ):
                if sharpness > current_entry["sharpness"]:
                    current_entry["hash"] = hash_value
                    current_entry["image"] = image.copy()
                    current_entry["sharpness"] = sharpness
                    current_entry["signature"] = signature
            else:
                slide_entries.append(current_entry)
                current_entry = make_slide_entry(hash_value, image, sharpness, signature)

        frame_id += 1

    if current_entry is not None:
        slide_entries.append(current_entry)

    cap.release()
    return [entry["image"] for entry in slide_entries]


def make_landscape_page(image):
    rgb_image = image.convert("RGB")

    if rgb_image.width >= rgb_image.height:
        return rgb_image

    page_size = (rgb_image.height, rgb_image.width)
    page = Image.new("RGB", page_size, "white")
    fitted_image = ImageOps.contain(rgb_image, page_size, RESAMPLING_FILTER)
    left = (page.width - fitted_image.width) // 2
    top = (page.height - fitted_image.height) // 2
    page.paste(fitted_image, (left, top))
    return page


def create_pdf_bytes(screenshots):
    if not screenshots:
        raise ValueError("There are no screenshots to export to PDF.")

    pages = [make_landscape_page(screenshot) for screenshot in screenshots]
    pdf_buffer = io.BytesIO()
    pages[0].save(
        pdf_buffer,
        format="PDF",
        save_all=True,
        append_images=pages[1:],
        resolution=PDF_DPI,
        quality=PDF_QUALITY,
        subsampling=0,
    )
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()


def main():
    st.set_page_config(
        page_title="YouTube Slides to PDF",
        layout="wide",
    )
    apply_page_style()
    render_hero()

    if "video_results" not in st.session_state:
        st.session_state["video_results"] = []

    input_column, settings_column = st.columns([2.15, 1], gap="large")

    with input_column:
        with st.container(border=True):
            st.markdown('<p class="section-kicker">Video queue</p>', unsafe_allow_html=True)
            youtube_urls = st.text_area(
                "YouTube URLs",
                "",
                height=190,
                placeholder="One YouTube URL per line",
                label_visibility="visible",
            )

    with settings_column:
        with st.container(border=True):
            st.markdown('<p class="section-kicker">Extraction settings</p>', unsafe_allow_html=True)
            capture_interval_seconds = st.number_input(
                "Capture interval in seconds",
                min_value=0.25,
                max_value=30.0,
                value=DEFAULT_CAPTURE_INTERVAL_SECONDS,
                step=0.25,
                help="Lower values capture more frames and may catch quick slide changes, but processing takes longer.",
            )
            hash_threshold = st.slider(
                "Consecutive duplicate merge strength",
                min_value=0,
                max_value=20,
                value=DEFAULT_DUPLICATE_MERGE_STRENGTH,
                help=(
                    "This is a similarity threshold, not a count of frames. The app compares "
                    "each sampled frame with the current slide candidate. Higher values merge "
                    "more similar consecutive frames; lower values keep more pages."
                ),
            )

    if st.button("Create PDFs for all videos", use_container_width=True):
        urls = parse_youtube_urls(youtube_urls)
        if not urls:
            st.warning("Enter at least one YouTube URL.")
            st.session_state["video_results"] = []
            return

        st.session_state["video_results"] = []
        results = []
        used_slugs = set()
        progress_bar = st.progress(0)
        st.divider()
        st.header("Results")
        result_slots = []

        for index, url in enumerate(urls, start=1):
            slot = st.empty()
            render_video_status(slot, index, len(urls), url, "Queued")
            result_slots.append(slot)

        with tempfile.TemporaryDirectory() as temp_root:
            for index, url in enumerate(urls, start=1):
                slot = result_slots[index - 1]
                video_dir = os.path.join(temp_root, f"video-{index}")
                os.makedirs(video_dir, exist_ok=True)

                def update_stage(stage, detail=None, current_slot=slot, current_index=index, current_url=url):
                    render_video_status(
                        current_slot,
                        current_index,
                        len(urls),
                        current_url,
                        stage,
                        detail,
                    )

                try:
                    result = process_youtube_video(
                        url,
                        video_dir,
                        capture_interval_seconds=capture_interval_seconds,
                        hash_threshold=hash_threshold,
                        stage_callback=update_stage,
                    )
                    file_slug = make_unique_slug(
                        slugify_filename(result["title"], fallback=f"youtube-video-{index}"),
                        used_slugs,
                    )
                    result["url"] = url
                    result["file_slug"] = file_slug
                    result["index"] = index
                    result["total"] = len(urls)
                    results.append(result)
                    st.session_state["video_results"] = results.copy()
                    render_video_result_slot(slot, result)
                except Exception as exc:
                    file_slug = make_unique_slug(f"youtube-video-{index}", used_slugs)
                    result = {
                        "url": url,
                        "file_slug": file_slug,
                        "error": str(exc),
                        "index": index,
                        "total": len(urls),
                    }
                    results.append(result)
                    st.session_state["video_results"] = results.copy()
                    render_video_result_slot(slot, result)

                progress_bar.progress(index / len(urls))

        st.session_state["video_results"] = results
        st.success(f"Finished processing {len(urls)} video(s).")

    elif st.session_state["video_results"]:
        st.divider()
        st.header("Results")
        for result in st.session_state["video_results"]:
            with st.container(border=True):
                render_video_result(result)


if __name__ == "__main__":
    main()
