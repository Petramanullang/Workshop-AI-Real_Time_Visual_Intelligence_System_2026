import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import json
import base64
import time

# ==========================================
# KONFIGURASI & SESSION STATE
# ==========================================
st.set_page_config(page_title="AI Vision Terminal", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

token_auth = st.secrets["API_KIE_KEY"]

if 'clear_trigger' not in st.session_state:
    st.session_state.clear_trigger = 0

# ==========================================
# CUSTOM CSS: DARK NEO BRUTALISM V2
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }
    
    /* Global App Background */
    .stApp {
        background-color: #0e1117;
    }

    /* Container Styling (Neo Brutalism) */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 3px solid #ffffff !important;
        border-radius: 0px !important;
        box-shadow: 6px 6px 0px #b9ff66 !important;
        background-color: #1a1c23 !important;
        padding: 1.5rem !important;
        transition: transform 0.2s ease;
    }
    
    /* Special styling for Display Panel */
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 6px 6px 0px #ff90e8 !important;
        background-color: #111317 !important;
        height: 400px;
    }

    /* Buttons */
    .stButton>button {
        border: 2px solid #ffffff !important;
        border-radius: 0px !important;
        background-color: #000000 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.15s ease !important;
    }
    .stButton>button:hover {
        transform: translate(-2px, -2px) !important;
        box-shadow: 4px 4px 0px #ff90e8 !important;
        color: #ff90e8 !important;
    }
    
    /* Primary Button */
    .stButton>button[kind="primary"] {
        background-color: #b9ff66 !important;
        color: #000000 !important;
        box-shadow: 4px 4px 0px #ffffff !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #a0f044 !important;
        color: #000000 !important;
        box-shadow: 6px 6px 0px #ffffff !important;
    }

    /* Inputs (Text Area & Uploader) */
    .stTextArea textarea {
        border: 2px solid #555 !important;
        border-radius: 0px !important;
        background-color: #222 !important;
        color: #fff !important;
        font-size: 1rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #b9ff66 !important;
        box-shadow: none !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 2px solid #333;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #888 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }
    .stTabs [aria-selected="true"] {
        color: #ff90e8 !important;
        border-bottom: 3px solid #ff90e8 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        border: 2px solid #444 !important;
        border-radius: 0px !important;
        background-color: #000 !important;
    }
    
    h1, h2, h3 { text-transform: uppercase; letter-spacing: -1px; }
    h1 { color: #ffffff !important; font-size: 2.5rem !important; margin-bottom: 0px !important;}
    h3 { color: #b9ff66 !important; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# FUNGSI-FUNGSI PENDUKUNG
# ==========================================
def create_placeholder_image(width=600, height=300, text="NO IMAGE"):
    img = Image.new('RGB', (width, height), color=(20, 20, 25))
    return img

def upload_image_to_api(image, filename):
    try:
        buffered = BytesIO()
        image.save(buffered, format=image.format if image.format else "PNG")
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        mime_type = f"image/{image.format.lower()}" if image.format else "image/png"
        base64_data = f"data:{mime_type};base64,{img_base64}"
        url = "https://kieai.redpandaai.co/api/file-base64-upload"
        payload = json.dumps({"base64Data": base64_data, "uploadPath": "images/base64", "fileName": filename})
        headers = {'Authorization': f'Bearer {token_auth}', 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=payload)
        response_json = response.json()
        if response_json.get("code", 0) == 200:
            return {'success': True, 'data': response_json["data"]}
        return {'success': False, 'error': response_json.get("msg", "Unknown error")}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def process_image_with_ai(image_url, prompt, aspect_ratio="1:1", resolution="1K"):
    try:
        url = "https://api.kie.ai/api/v1/jobs/createTask"
        input_data = {"prompt": prompt, "aspect_ratio": aspect_ratio, "resolution": resolution, "nsfw_checker": False}
        if image_url:
            input_data["input_urls"] = [image_url]
            model = "flux-2/pro-image-to-image"
        else:
            model = "flux-2/pro-text-to-image"
            
        payload = json.dumps({"model": model, "callBackUrl": "", "input": input_data})
        headers = {'Authorization': f'Bearer {token_auth}', 'Content-Type': 'application/json'}
        response = requests.post(url, headers=headers, data=payload)
        response_json = response.json()
        if response_json.get("code", 0) == 200:
            return {'success': True, 'data': response_json["data"]}
        return {'success': False, 'error': response_json.get("msg", "Unknown error")}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_task_detail(task_id):
    try:
        url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
        headers = {'Authorization': f'Bearer {token_auth}'}
        response = requests.get(url, headers=headers)
        response_json = response.json()
        if response_json.get("code", 0) == 200:
            return {'success': True, 'data': response_json["data"]}
        return {'success': False, 'error': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ==========================================
# UI: HEADER & MAIN LAYOUT (4:8 GRID)
# ==========================================
st.markdown("<h1>⚡ VISUAL INTELLIGENCE</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #888; font-size: 1.1rem;'>Real-Time AI-Powered Vision Interface.</p>", unsafe_allow_html=True)
st.write("") # Spacer

col_control, col_display = st.columns([4, 8], gap="large")

image_obj = None 

# ==========================================
# KOLOM KIRI: CONTROL PANEL
# ==========================================
with col_control:
    with st.container(border=True):
        st.subheader("⚙️ PARAMETERS")
        
        uploaded_file = st.file_uploader(
            "UPLOAD SOURCE",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=False,
            key=f"file_uploader_{st.session_state.clear_trigger}"
        )
        
        if uploaded_file:
            image_obj = Image.open(uploaded_file)
            st.caption(f"✓ Loaded: {uploaded_file.name} ({image_obj.width}x{image_obj.height})")
        
        text_input = st.text_area(
            "PROMPT INSTRUCTION *",
            placeholder="Describe the image modifications or generation here...",
            key=f"text_area_{st.session_state.clear_trigger}",
            height=120
        )
        
        with st.expander("🛠️ Advanced Settings"):
            sel_res = st.selectbox("Resolution", ["1K", "2K", "4K"], key=f"res_{st.session_state.clear_trigger}")
            sel_ar = st.selectbox("Aspect Ratio", ["1:1", "16:9", "9:16", "4:3"], key=f"ar_{st.session_state.clear_trigger}")

        st.write("") # Spacer
        
        btn_col1, btn_col2 = st.columns([1, 2])
        with btn_col1:
            clear_button = st.button("RESET", use_container_width=True)
        with btn_col2:
            submit_button = st.button("EXECUTE", type="primary", use_container_width=True)

if clear_button:
    st.session_state.clear_trigger += 1
    st.rerun()

# ==========================================
# KOLOM KANAN: DISPLAY CANVAS & TABS
# ==========================================
with col_display:
    with st.container(border=True):
        
        tab_src, tab_res = st.tabs(["🖼️ SOURCE", "✨ RESULT"])
        
        with tab_src:
            src_placeholder = st.empty()
            if image_obj:
                src_placeholder.image(image_obj, use_container_width=True)
            else:
                src_placeholder.image(create_placeholder_image(), use_container_width=True)
                
        with tab_res:
            res_placeholder = st.empty()
            res_placeholder.image(create_placeholder_image(), use_container_width=True)
            
            # Area untuk status & download
            status_container = st.empty()
            action_container = st.container()

# ==========================================
# LOGIKA EKSEKUSI & RENDER
# ==========================================
if submit_button:
    if not text_input.strip():
        with col_control:
            st.error("⚠️ PROMPT REQUIRED!")
    else:
        with status_container:
            st.info("🚀 INITIALIZING SEQUENCE...")
            progress_bar = st.progress(0)
            
        image_url = None
        upload_success = True

        # Tahap 1: Upload (Jika ada)
        if uploaded_file and image_obj:
            with status_container:
                st.info("📤 UPLOADING SOURCE IMAGE...")
                progress_bar.progress(10)
                
            result = upload_image_to_api(image_obj, uploaded_file.name)
            if result['success']:
                image_url = result['data'].get('downloadUrl', '')
                progress_bar.progress(30)
            else:
                upload_success = False
                with status_container:
                    st.error("❌ UPLOAD FAILED.")

        # Tahap 2: AI Processing
        if upload_success:
            with status_container:
                st.info("🧠 CREATING AI TASK...")
                
            process_result = process_image_with_ai(image_url, text_input, aspect_ratio=sel_ar, resolution=sel_res)

            if process_result.get('success'):
                task_id = process_result['data'].get('taskId')
                if task_id:
                    max_attempts = 30
                    is_timeout = True

                    # Tahap 3: Polling
                    for attempt in range(1, max_attempts + 1):
                        progress_val = min(30 + (attempt * 2), 95) # Animasi progress
                        progress_bar.progress(progress_val)
                        
                        with status_container:
                            st.warning(f"⏳ RENDERING... (Attempt {attempt}/{max_attempts}) | Task: {task_id}")
                        
                        detail_result = get_task_detail(task_id)
                        if detail_result['success']:
                            task_status = detail_result.get('data', {}).get('state', '')

                            if task_status == 'success':
                                progress_bar.progress(100)
                                with status_container:
                                    st.success("✨ RENDER COMPLETE!")
                                
                                result_urls = json.loads(detail_result['data'].get('resultJson', '{}')).get('resultUrls', [])
                                if result_urls:
                                    output_image_url = result_urls[0]
                                    res_placeholder.image(output_image_url, use_container_width=True)
                                    
                                    with action_container:
                                        try:
                                            img_data = requests.get(output_image_url).content
                                            st.download_button(
                                                label="💾 DOWNLOAD HI-RES",
                                                data=img_data,
                                                file_name=f"ai_render_{task_id}.png",
                                                mime="image/png",
                                                use_container_width=True,
                                                type="primary"
                                            )
                                        except:
                                            st.markdown(f"**[Click Here to Download]({output_image_url})**")
                                
                                is_timeout = False
                                break
                            
                            elif task_status == 'fail':
                                with status_container:
                                    st.error("❌ RENDER FAILED.")
                                is_timeout = False
                                break
                        
                        time.sleep(5)

                    if is_timeout:
                        with status_container:
                            st.error(f"⏰ TIMEOUT. Please try again.")
                else:
                    with status_container:
                        st.error("❌ ERROR: Task ID not generated.")
            else:
                with status_container:
                    st.error("❌ ERROR: Failed to communicate with AI endpoint.")