import os
import tempfile
import zipfile
import fitz
import pandas as pd

# --- SET FIXED VALUES HERE ---
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
                fontname="helv",   # Use built-in Helvetica font
                fontsize=PREFERRED_SIZE,
                color=(0, 0, 0),
                align=1,
            )
            if rc < 0:
                rc = page.insert_textbox(
                    new_rect,
                    replace_str,
                    fontname="helv",
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
    original_folder = os.path.dirname(data_path)
    if ext == '.pdf':
        outname = f"{base}_replaced.pdf"
        outpath_temp = os.path.join(temp_dir, outname)
        outpath_same = os.path.join(original_folder, outname)
        process_pdf(data_path, outpath_temp, search_str, replace_str)
        process_pdf(data_path, outpath_same, search_str, replace_str)
        return outpath_temp
    elif ext == '.csv':
        outname = f"{base}_replaced.csv"
        outpath_temp = os.path.join(temp_dir, outname)
        outpath_same = os.path.join(original_folder, outname)
        process_csv(data_path, outpath_temp, search_str, replace_str)
        process_csv(data_path, outpath_same, search_str, replace_str)
        return outpath_temp
    elif ext == '.xpt':
        outname = f"{base}_replaced.xpt"
        outpath_temp = os.path.join(temp_dir, outname)
        outpath_same = os.path.join(original_folder, outname)
        process_xpt(data_path, outpath_temp, search_str, replace_str)
        process_xpt(data_path, outpath_same, search_str, replace_str)
        return outpath_temp
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
        # Also save replaced ZIP in same folder as input ZIP
        original_folder = os.path.dirname(file_path)
        zip_path_same = os.path.join(original_folder, "replaced_files.zip")
        with open(zip_path, "rb") as src, open(zip_path_same, "wb") as dst:
            dst.write(src.read())
        return zip_path, "replaced_files.zip"
    else:
        out = process_one(file_path, filename, search_str, replace_str, temp_dir)
        if out:
            return out, os.path.basename(out)
        else:
            return None, None

def main():
    print("Bulk Text Replacer (PDF, CSV, XPT, ZIP)")
    search_str = input("Enter the text to search for: ")
    replace_str = input("Enter the text to replace with: ")
    file_path = input("Enter the filename or path (e.g., sample.pdf, data/test.csv, etc.): ")

    if not os.path.exists(file_path):
        print("Error: File does not exist in the given path.")
    else:
        output_path, output_name = run_process(search_str, replace_str, file_path)
        if output_path and os.path.exists(output_path):
            print(f"Done! The file '{output_name}' was saved in the same folder as your original file.")
        else:
            print("Processing failed or unsupported file type.")

if __name__ == '__main__':
    main()
