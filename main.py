import streamlit as st
import io
import zipfile


# IMPORT YOUR MODULES
from sections import (transaction_id, 
                      student_identity, student_non_financial,
                      student_demographics,student_financials)

# COMBINE INTO MASTER LAYOUT
FULL_LAYOUT = {
    "Transaction Identification": transaction_id.LAYOUT,
    "Student Identity and Contact": student_identity.LAYOUT,
    "Student Non-Financial Information": student_non_financial.LAYOUT,
    "Student Demographic Information": student_demographics.LAYOUT,
    "Student Manually Entered Financial": student_financials.LAYOUT
}

# NSLDS Type 1 Record Mapping (Static link to ISIR field keys)
NSLDS_MAP = {
    "ssn": {"isir_f": "f30", "pos": (2, 10), "len": 9, "type": "num"},
    "first": {"isir_f": "f25", "pos": (11, 25), "len": 15, "type": "alpha"},
    "last": {"isir_f": "f27", "pos": (26, 60), "len": 35, "type": "alpha"},
    "dob": {"isir_f": "f29", "pos": (61, 68), "len": 8, "type": "num"},
}

# --- LOGIC FUNCTIONS ---
def parse_isir_to_state(raw_content):
    clean_raw = raw_content.replace('\r', '').replace('\n', '')
    original_values = {}
    for section in FULL_LAYOUT.values():
        for key, meta in section.items():
            start, end = meta["pos"]
            val = clean_raw[start-1:end].strip()
            st.session_state[f"input_{key}"] = val
            original_values[key] = val
    st.session_state.original_snapshot = original_values

def get_isir_string():
    base = st.session_state.get("full_raw_string", " " * 7704).replace('\r', '').replace('\n', '')
    buffer = list(base.ljust(7704)[:7704])
    for section in FULL_LAYOUT.values():
        for key, meta in section.items():
            val = str(st.session_state.get(f"input_{key}", ""))
            start, end = meta["pos"][0], meta["pos"][1]
            length = meta["len"]
            formatted = val.zfill(length)[:length] if meta["type"] == "num" else val.ljust(length)[:length]
            buffer[start-1:end] = list(formatted)
    return "".join(buffer)[:7704]

def get_nslds_string():
    buffer = list("1" + (" " * 549)) 
    for key, meta in NSLDS_MAP.items():
        val = str(st.session_state.get(f"input_{meta['isir_f']}", ""))
        start, end, length = meta["pos"][0], meta["pos"][1], meta["len"]
        formatted = val.zfill(length)[:length] if meta["type"] == "num" else val.ljust(length)[:length]
        buffer[start-1:end] = list(formatted)
    return "".join(buffer).rstrip() + "\r\n"

# --- UI INITIALIZATION ---
st.set_page_config(page_title="SFP Student Automator", layout="wide")
if "original_snapshot" not in st.session_state:
    st.session_state.original_snapshot = {}

st.title("ISIR & NSLDS Production Tool")
uploaded_file = st.file_uploader("Upload Student ISIR (.dat)", type=["dat"])

if uploaded_file and "file_processed" not in st.session_state:
    raw_str = uploaded_file.read().decode("utf-8")
    st.session_state.full_raw_string = raw_str
    parse_isir_to_state(raw_str)
    st.session_state.file_processed = True
    st.rerun()

# --- TABS GENERATION ---
tab_titles = list(FULL_LAYOUT.keys())
tabs = st.tabs(tab_titles)
original_snap = st.session_state.get("original_snapshot", {})

for idx, section_name in enumerate(tab_titles):
    with tabs[idx]:
        fields = FULL_LAYOUT[section_name]
        cols = st.columns(3)
        for i, (key, meta) in enumerate(fields.items()):
            col = cols[i % 3]
            field_num = key.replace('f', '')
            curr_val = st.session_state.get(f"input_{key}", "")
            orig_val = original_snap.get(key, "")
            is_edited = (curr_val != orig_val) and (uploaded_file is not None)
            l_color = "#FF0000" if is_edited else "#000000"
            
            with col:
                st.markdown(f"""
                    <div style='margin-bottom:-15px; margin-top:15px;'>
                        <p style='color:{l_color}!important; opacity:1!important; font-size:18px!important; font-weight:800!important;'>
                            {field_num}. {meta['label']}
                        </p>
                    </div>""", unsafe_allow_html=True)
                st.text_input(label=key, label_visibility="collapsed", key=f"input_{key}", max_chars=meta["len"])
                if is_edited:
                    st.markdown(f"<p style='color:red; font-size:11px; margin-top:-10px;'>Modified (Was: '{orig_val}')</p>", unsafe_allow_html=True)
                st.caption(f"Length: {len(curr_val)}/{meta['len']}")

# --- BUTTON FOOTER ---
st.divider()
b1, b2, b3 = st.columns(3)
isir_data = get_isir_string()
nslds_data = get_nslds_string()

with b1:
    st.download_button("📥 Download ISIR (.dat)", isir_data.encode('utf-8'), "Student_ISIR.dat", use_container_width=True)
with b2:
    st.download_button("📄 Download NSLDS (.txt)", nslds_data.encode('utf-8'), "Student_NSLDS.txt", use_container_width=True)
with b3:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "x") as pkg:
        pkg.writestr("Student_ISIR.dat", isir_data.encode('utf-8'))
        pkg.writestr("Student_NSLDS.txt", nslds_data.encode('utf-8'))
    st.download_button("📦 Download Both (ZIP)", buf.getvalue(), "SFP_Student_Package.zip", use_container_width=True)