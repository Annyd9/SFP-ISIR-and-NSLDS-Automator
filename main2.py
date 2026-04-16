import streamlit as st
import io
import zipfile

# 1. MODULAR IMPORTS
from sections import (
    transaction_id, 
    student_identity, 
    student_non_financial, 
    student_demographics,
    student_financials
)

# 2. MASTER ASSEMBLY
FULL_LAYOUT = {
    "Transaction Identification": transaction_id.LAYOUT,
    "Student Identity and Contact": student_identity.LAYOUT,
    "Student Non-Financial Information": student_non_financial.LAYOUT,
    "Student Demographic Information": student_demographics.LAYOUT,
    "Student Manually Entered Financial": student_financials.LAYOUT
}

NSLDS_MAP = {
    "ssn": {"isir_f": "f30", "pos": (2, 10), "len": 9, "type": "num"},
    "first": {"isir_f": "f25", "pos": (11, 25), "len": 15, "type": "alpha"},
    "last": {"isir_f": "f27", "pos": (26, 60), "len": 35, "type": "alpha"},
    "dob": {"isir_f": "f29", "pos": (61, 68), "len": 8, "type": "num"},
}

# --- LOGIC ENGINE ---
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
    """Rebuilds the 7704-character fixed-width string with strict padding."""
    # Start with a clean base of spaces
    base = st.session_state.get("full_raw_string", " " * 7704).replace('\r', '').replace('\n', '')
    buffer = list(base.ljust(7704)[:7704])
    
    for section in FULL_LAYOUT.values():
        for key, meta in section.items():
            # Get current value from UI state
            val = str(st.session_state.get(f"input_{key}", ""))
            start, end = meta["pos"][0], meta["pos"][1]
            length = meta["len"]
            
            # STRICT FORMATTING: 
            # 1. Truncate value if it's somehow longer than allowed
            # 2. Pad to EXACT length (Numeric = leading zeros, Alpha = trailing spaces)
            if meta["type"] == "num":
                formatted = val.strip().zfill(length)[-length:]
            else:
                formatted = val.strip().ljust(length)[:length]
            
            # Place into buffer at the precise index
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
st.set_page_config(page_title="SFP Production Tool", layout="wide")

if "original_snapshot" not in st.session_state:
    st.session_state.original_snapshot = {}

# --- HEADER SECTION (Title + Upload Button) ---
title_col, upload_col = st.columns([3, 1])

with title_col:
    st.title("ISIR & NSLDS Production Tool")

with upload_col:
    st.write("##") 
    uploaded_file = st.file_uploader("Upload .dat", type=["dat"], label_visibility="collapsed")

if uploaded_file and "file_processed" not in st.session_state:
    raw_str = uploaded_file.read().decode("utf-8")
    st.session_state.full_raw_string = raw_str
    parse_isir_to_state(raw_str)
    st.session_state.file_processed = True
    st.rerun()

st.write("---")

# --- SIDEBAR (Export Controls Only) ---
with st.sidebar:
    st.header("📤 Export Tools")
    
    final_isir = get_isir_string()
    final_nslds = get_nslds_string()
    
    st.download_button("📥 Download ISIR (.dat)", final_isir.encode('utf-8'), "Student_ISIR.dat", use_container_width=True)
    st.download_button("📄 Download NSLDS (.txt)", final_nslds.encode('utf-8'), "Student_NSLDS.txt", use_container_width=True)
    
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "x") as pkg:
        pkg.writestr("Student_ISIR.dat", final_isir.encode('utf-8'))
        pkg.writestr("Student_NSLDS.txt", final_nslds.encode('utf-8'))
    st.download_button("📦 Download Both (ZIP)", zip_buf.getvalue(), "SFP_Package.zip", use_container_width=True)
    
    st.divider()
    if st.button("🗑️ Clear All Data", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.session_state.original_snapshot = {}
        st.rerun()

# --- MAIN WORKSPACE (Tabs) ---
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
            
            # Colour change logic: Red if modified, Black if original
            is_edited = (curr_val != orig_val) and ("full_raw_string" in st.session_state)
            l_color = "#FF0000" if is_edited else "#000000"
            
            with col:
                st.markdown(f"""
                    <div style='margin-bottom:-12px; margin-top:15px;'>
                        <p style='color:{l_color}!important; opacity:1!important; font-size:19px!important; font-weight:800!important;'>
                            {field_num}. {meta['label']}
                        </p>
                    </div>""", unsafe_allow_html=True)
                
                # The text cell
                st.text_input(label=key, label_visibility="collapsed", key=f"input_{key}", max_chars=meta["len"])
                
                # "Modified (Was: ...)" functionality removed here
                st.caption(f"Length: {len(curr_val)}/{meta['len']}")