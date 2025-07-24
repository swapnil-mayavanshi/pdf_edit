import os
import tempfile
import zipfile
import fitz
import pandas as pd
import streamlit as st

# --- SET FIXED VALUES HERE ---
FONT_PATH = "times.ttf"
PREFERRED_SIZE = 11
EXPAND = 2.5
Y_SHIFT = 1.5
# -----------------------------

def process_pdf(pdf_path, output_path, search_str, replace_str):
    doc = fitz.open(pdf_path)
    for page in doc:
        text_instances = page.search_for(search_str)
        for rect in text_instances:
            new_rect = fitz.Rect(
                rect.x0 - EXPAND,
                rect.y0 + Y_SHIFT - 1,
                rect.x1 + EXPAND,
                rect.y1 + Y_SHIFT + 1
            )
            page.draw_rect(new_rect, color=(1, 1, 1), fill=(1, 1, 1))
            rc = page.insert_textbox(
                new_rect,
                replace_str,
                fontname="TimesNewRomanPSMT",
                fontfile=FONT_PATH,
                fontsize=PREFERRED_SIZE,
                color=(0, 0, 0),
                align=1,
            )
            if rc < 0:
                rc = page.insert_textbox(
                    new_rect,
                    replace_str,
                    fontname="TimesNewRomanPSMT",
                    fontfile=FONT_PATH,
                    fontsize=PREFERRED_SIZE - 1,
                    color=(0, 0, 0),
                    align=1,
                )
    doc.save(output_path)
    doc.close()
    return output_path

def process_csv(csv_path, output_path, search_str, replace_str):
    df = pd.read_csv(csv_path, dtype=str, encoding='utf-8', engine='python')
    df = df.applymap(lambda x: x.replace(search_str, replace_str) if isinstance(x, str) else x)
    df.to_csv(output_path, index=False, encoding='utf-8')
    return output_path

def process_xpt(xpt_path, output_path, search_str, replace_str):
    df = pd.read_sas(xpt_path, format='xport', encoding='utf-8')
    df = df.applymap(lambda x: x.replace(search_str, replace_str) if isinstance(x, str) else x)
    df.to_xpt(output_path, index=False)
    return output_path

def process_one(data_path, filename, search_str, replace_str, temp_dir):
    ext = os.path.splitext(filename)[1].lower()
    base = os.path.splitext(os.path.basename(filename))[0]
    if ext == '.pdf':
        outpath = os.path.join(temp_dir, f"{base}_replaced.pdf")
        process_pdf(data_path, outpath, search_str, replace_str)
        return outpath
    elif ext == '.csv':
        outpath = os.path.join(temp_dir, f"{base}_replaced.csv")
        process_csv(data_path, outpath, search_str, replace_str)
        return outpath
    elif ext == '.xpt':
        outpath = os.path.join(temp_dir, f"{base}_replaced.xpt")
        process_xpt(data_path, outpath, search_str, replace_str)
        return outpath
    else:
        return None

def run_process(search_str, replace_str, file_path):
    temp_dir = tempfile.mkdtemp()
    processed_files = []
    file_ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    if file_ext == '.zip':
        with zipfile.ZipFile(file_path, 'r') as zin:
            zin.extractall(temp_dir)
            for f in zin.namelist():
                fpath = os.path.join(temp_dir, f)
                out = process_one(fpath, f, search_str, replace_str, temp_dir)
                if out: processed_files.append(out)
        zip_path = os.path.join(temp_dir, "replaced_files.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zout:
            for f in processed_files:
                zout.write(f, arcname=os.path.basename(f))
        return zip_path, "replaced_files.zip"
    else:
        out = process_one(file_path, filename, search_str, replace_str, temp_dir)
        if out:
            return out, os.path.basename(out)
        else:
            return None, None

# ---- Streamlit UI ----
st.title("Bulk Text Replacer (PDF, CSV, XPT, ZIP)")
st.write("Type the filename (with extension) or path, enter the search and replace strings, and download the processed file.")

search_str = st.text_input("Search for:")
replace_str = st.text_input("Replace with:")
file_path = st.text_input("Enter filename or path (e.g., 'sample.pdf', 'data/test.csv', etc.):")

if st.button("Run") and search_str and replace_str and file_path:
    with st.spinner("Processing..."):
        if not os.path.exists(file_path):
            st.error("File does not exist in the given path.")
        else:
            output_path, output_name = run_process(search_str, replace_str, file_path)
            if output_path and os.path.exists(output_path):
                with open(output_path, "rb") as f:
                    st.success(f"Done! Download your file: {output_name}")
                    st.download_button(
                        label=f"Download {output_name}",
                        data=f,
                        file_name=output_name
                    )
            else:
                st.error("Processing failed or unsupported file type.")

st.info("Supported input: PDF, CSV, XPT, or ZIP containing any of these file types. The file should be in the same folder as this app or provide the relative path.")
