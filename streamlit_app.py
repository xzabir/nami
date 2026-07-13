import streamlit as st
import time
import tempfile
import os

# Set page config
st.set_page_config(
    page_title="Nami | AI Video Captioning",
    page_icon="🌊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for minimalist glassmorphism aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global styling */
    .stApp {
        background-color: #08060d;
        color: #f9fafb;
        font-family: 'Inter', sans-serif;
        background-image: 
            radial-gradient(at 0% 0%, rgba(170, 59, 255, 0.08) 0px, transparent 50%),
            radial-gradient(at 100% 100%, rgba(170, 59, 255, 0.06) 0px, transparent 50%);
        background-attachment: fixed;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #f9fafb !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    h1 {
        font-size: 3.5rem !important;
        letter-spacing: -0.04em !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Input fields & Uploader */
    .stTextInput input, .stFileUploader {
        background-color: rgba(25, 25, 30, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f9fafb !important;
        border-radius: 8px !important;
        backdrop-filter: blur(12px);
    }
    .stTextInput input:focus {
        border-color: #c084fc !important;
        box-shadow: 0 0 0 3px rgba(192, 132, 252, 0.15) !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #f9fafb !important;
        color: #08060d !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #9ca3af !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 24px -6px rgba(0, 0, 0, 0.4);
    }
    
    /* Cards for captions */
    .caption-card {
        background-color: rgba(25, 25, 30, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        backdrop-filter: blur(16px);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .caption-card:hover {
        transform: translateY(-2px);
        border-color: rgba(192, 132, 252, 0.4);
        box-shadow: 0 12px 48px -8px rgba(0, 0, 0, 0.6);
    }
    .caption-title {
        color: #c084fc;
        font-size: 0.75rem;
        font-family: ui-monospace, Consolas, monospace;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
        background: rgba(192, 132, 252, 0.15);
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        border: 1px solid rgba(192, 132, 252, 0.4);
    }
    .caption-text {
        font-size: 1rem;
        line-height: 1.6;
        color: #f9fafb;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌊 Nami")
st.markdown("<p style='color: #9ca3af; font-size: 1.1rem; max-width: 600px;'>Drop in a video URL and Nami watches it frame by frame with Gemma 3's vision model to write four zero-rewrite caption styles.</p>", unsafe_allow_html=True)
st.markdown("---")

# Import backend logic safely
try:
    from app.services.caption_engine import generate_captions
    from app.config import settings
except ImportError as e:
    st.error(f"Failed to load backend modules: {e}. Make sure you run this from the project root.")
    st.stop()

# Load API key from Streamlit secrets if available (to fix the No API Key error on cloud)
if "FIREWORKS_API_KEY" in st.secrets:
    settings.fireworks_api_key = st.secrets["FIREWORKS_API_KEY"]

# Input area
tab1, tab2 = st.tabs(["🔗 Paste URL", "📁 Upload File"])

video_url = None
uploaded_file = None

with tab1:
    video_url = st.text_input("Video URL", placeholder="https://storage.example.com/clips/clip1.mp4")

with tab2:
    uploaded_file = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "webm"])

st.markdown("<br>", unsafe_allow_html=True)
generate_btn = st.button("Generate Captions", use_container_width=True)

if generate_btn:
    source_to_process = None
    temp_path = None
    
    if uploaded_file is not None:
        # Save uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name
            source_to_process = temp_path
    elif video_url:
        source_to_process = video_url
        
    if not source_to_process:
        st.warning("Please provide a video URL or upload a file first.")
    else:
        with st.spinner("Analyzing frames and generating captions..."):
            try:
                start_time = time.time()
                
                # generate_captions expects a string URL/path
                captions = generate_captions(source_to_process, ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"])
                
                elapsed = time.time() - start_time
                
                st.success(f"Captions generated successfully in {elapsed:.1f} seconds.")
                
                # Display results in beautiful cards
                styles = {
                    "formal": ("Formal", captions.get("formal", "")),
                    "sarcastic": ("Sarcastic", captions.get("sarcastic", "")),
                    "humorous_tech": ("Humorous · Tech", captions.get("humorous_tech", "")),
                    "humorous_non_tech": ("Humorous · Non-tech", captions.get("humorous_non_tech", ""))
                }
                
                cols = st.columns(2)
                
                for idx, (key, (title, text)) in enumerate(styles.items()):
                    col = cols[idx % 2]
                    with col:
                        st.markdown(f"""
                        <div class="caption-card">
                            <div class="caption-title">{title}</div>
                            <div class="caption-text">{text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"Error processing video: {str(e)}")
            finally:
                # Clean up temp file if we created one
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #9ca3af; font-family: ui-monospace, monospace; font-size: 0.75rem;'>Nami — AMD Developer Hackathon, Track 2<br>Gemma 3 · Streamlit</div>", unsafe_allow_html=True)
