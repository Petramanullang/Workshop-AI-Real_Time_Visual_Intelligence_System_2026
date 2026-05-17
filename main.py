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
token_auth = st.secrets["API_KIE_KEY"] # Ganti dengan token API milikmu

# Initialize session state untuk clear functionality (Tahap 8)
if 'clear_trigger' not in st.session_state:
    st.session_state.clear_trigger = 0


# ==========================================
# FUNGSI-FUNGSI PENDUKUNG
# ==========================================

# Tahap 7: Fungsi untuk membuat placeholder image
def create_placeholder_image(width=400, height=400):
    try:
        placeholder_url = "https://static.vecteezy.com/system/resources/previews/022/059/000/non_2x/no-image-available-icon-vector.jpg"
        response = requests.get(placeholder_url, timeout=5)
        
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            return img
        else:
            img = Image.new('RGB', (width, height), color=(240, 240, 240))
            return img
    except Exception as e:
        print(f"Error loading placeholder: {e}")
        img = Image.new('RGB', (width, height), color=(240, 240, 240))
        return img

# Tahap 11: Fungsi untuk upload gambar ke API
def upload_image_to_api(image, filename):
    try:
        buffered = BytesIO()
        image.save(buffered, format=image.format if image.format else "PNG")
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        mime_type = f"image/{image.format.lower()}" if image.format else "image/png"
        base64_data = f"data:{mime_type};base64,{img_base64}"
        
        url = "https://kieai.redpandaai.co/api/file-base64-upload"
        
        payload = json.dumps({
            "base64Data": base64_data,
            "uploadPath": "images/base64",
            "fileName": filename
        })
        
        headers = {
            'Authorization': f'Bearer {token_auth}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, data=payload)
        response_json = response.json()
        
        if response_json.get("code", 0) == 200:
            return {'success': True, 'status': response.status_code, 'data': response_json["data"]}
        else:
            return {'success': False, 'status': response.status_code, 'error': response_json.get("msg", "Unknown error")}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Tahap 13: Fungsi untuk proses gambar dengan AI
def process_image_with_ai(image_url, prompt, aspect_ratio="1:1", resolution="1K"):
    try:
        url = "https://api.kie.ai/api/v1/jobs/createTask"
        
        input_data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "nsfw_checker": False
        }
        
        if image_url:
            input_data["input_urls"] = [image_url]
            model = "flux-2/pro-image-to-image"
        else:
            model = "flux-2/pro-text-to-image"
        
        payload = json.dumps({
            "model": model,
            "callBackUrl": "",
            "input": input_data
        })
        
        headers = {
            'Authorization': f'Bearer {token_auth}',
            'Content-Type': 'application/json' # Diperbaiki dari stretch-Type
        }
        
        response = requests.post(url, headers=headers, data=payload)
        response_json = response.json()
        
        if response_json.get("code", 0) == 200:
            return {'success': True, 'data': response_json["data"]}
        else:
            return {'success': False, 'status': response.status_code, 'error': response_json.get("msg", "Unknown error")}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# Tahap 16: Fungsi untuk mendapatkan detail task
def get_task_detail(task_id):
    try:
        url = f"https://api.kie.ai/api/v1/jobs/recordInfo?taskId={task_id}"
        headers = {'Authorization': f'Bearer {token_auth}'}
        
        response = requests.get(url, headers=headers)
        response_json = response.json()

        if response_json.get("code", 0) == 200:
            return {'success': True, 'data': response_json["data"]}
        else:
            return {'success': False, 'status': response.status_code, 'error': response.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ==========================================
# ANTARMUKA PENGGUNA (UI) STREAMLIT
# ==========================================

# Tahap 1
st.title("AI-powered Vision App")
st.write("Upload your image. The app uses 'image.jpg' as the target when it exists, then shows the output below.")

# Tahap 2, 3, 4
with st.container(border=True):
    st.subheader("Input")
    st.write("Image upload")

    uploaded_file = st.file_uploader(
        "Drop an image here or choose a file",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        key=f"file_uploader_{st.session_state.clear_trigger}"
    )
    
    text_input = st.text_area(
        "Masukkan teks/prompt Anda: *",
        placeholder="Ketik instruksi atau deskripsi di sini...",
        key=f"text_area_{st.session_state.clear_trigger}"
    )

    # Tahap 5
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        clear_button = st.button("Clear", use_container_width=True)
    with btn_col2:
        submit_button = st.button("Render", type="primary", use_container_width=True)

# Tahap 8 (Aksi Tombol Clear)
if clear_button:
    st.session_state.clear_trigger += 1
    st.rerun()

# Tahap 6 & 10
col1, col2 = st.columns(2, border=True)

image_obj = None # Variabel penampung objek gambar
with col1:
    st.subheader("Image upload")
    input_placeholder = st.empty()

    if uploaded_file:
        image_obj = Image.open(uploaded_file)
        input_placeholder.image(image_obj, use_container_width=True)
    else:
        placeholder_img = create_placeholder_image()
        input_placeholder.image(placeholder_img, use_container_width=True)

with col2:
    st.subheader("Output")
    output_placeholder = st.empty()
    
    placeholder_img = create_placeholder_image()
    output_placeholder.image(placeholder_img, use_container_width=True)


# ==========================================
# LOGIKA EKSEKUSI & POLLING API
# ==========================================

# Tahap 9
if submit_button:
    if not text_input or text_input.strip() == "":
        st.error("⚠️ Mohon isi teks/prompt terlebih dahulu!")
    else:
        # Tahap 14: Menampilkan Spinner
        with st.spinner("🎨 Memproses gambar dengan AI..."):
            image_url = None
            upload_success = True

            # Tahap 11 & 12: Upload Gambar Jika Ada
            if uploaded_file and image_obj:
                st.info("Mengunggah gambar ke server penyimpanan...")
                result = upload_image_to_api(image_obj, uploaded_file.name)
                
                if result['success']:
                    st.success("✓ Upload gambar berhasil")
                    st.write(f"**Nama file:** {result['data'].get('fileName', uploaded_file.name)}")
                    st.write(f"**Ukuran:** {result['data'].get('fileSize', uploaded_file.size)} bytes")
                    
                    image_url = result['data'].get('downloadUrl', '')
                else:
                    upload_success = False
                    if 'error' in result:
                        st.error(f"Gagal memproses gambar: {result['error']}")
                    else:
                        st.error(f"Gagal upload: Status {result['status']}")

            # Lanjut ke AI jika tidak ada gambar (text-to-image) ATAU upload gambar berhasil (image-to-image)
            if upload_success:
                process_result = process_image_with_ai(image_url, text_input)

                if process_result.get('success'):
                    # Tahap 15: Mengambil Task ID
                    response_data = process_result['data'] or {}
                    task_id = response_data.get('data', {}).get('taskId') or response_data.get('taskId')

                    if task_id:
                        st.info(f"Task ID API: {task_id}")
                        
                        # Tahap 16: Polling Status Task
                        max_attempts = 60
                        time_sleep = 10
                        status_text = st.empty()
                        is_timeout = True

                        for attempt in range(1, max_attempts + 1):
                            status_text.text(f"Mengecek status task... (Percobaan {attempt}/{max_attempts})")
                            
                            detail_result = get_task_detail(task_id)
                            if detail_result['success']:
                                task_data = detail_result.get('data', {})
                                task_status = task_data.get('state', '')

                                # Tahap 17: Status Success
                                if task_status == 'success':
                                    status_text.empty()
                                    st.success("✓ Proses AI berhasil!")
                                    
                                    result_urls = json.loads(task_data.get('resultJson', '{}')).get('resultUrls', [])
                                    if result_urls:
                                        output_image_url = result_urls[0]
                                        output_placeholder.image(output_image_url, use_container_width=True)
                                        st.write(f"**Output URL:** {output_image_url}")
                                    else:
                                        st.warning("Result URL tidak ditemukan pada response JSON")
                                    
                                    is_timeout = False
                                    break
                                
                                # Tahap 19: Status Fail
                                elif task_status == 'fail':
                                    status_text.empty()
                                    st.error(f"Task gagal dengan status: {task_status}")
                                    error_message = task_data.get('errorMessage', 'Unknown error')
                                    st.write(f"**Error Message:** {error_message}")
                                    
                                    is_timeout = False
                                    break
                            else:
                                st.warning(f"Gagal mengecek status: {detail_result.get('error', 'Unknown error')}")
                            
                            time.sleep(time_sleep)

                        # Tahap 19: Timeout
                        if is_timeout:
                            status_text.empty()
                            st.warning("⏰ Timeout: Task masih dalam proses AI. Silakan coba cek lagi nanti.")
                            st.write(f"Task ID Anda: {task_id}")

                    else:
                        st.error("Task ID tidak ditemukan dalam response")
                        st.write(f"**Response mentah:** {response_data}")
                else:
                    st.error(f"Gagal membuat task AI. Mohon coba lagi. Error: {process_result.get('error')}")