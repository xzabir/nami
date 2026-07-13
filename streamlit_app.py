import streamlit as st
import asyncio
import time

# Set page config for a wider, modern layout
st.set_page_config(
    page_title="Nami | AI Video Captioning",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS to mimic a modern, sleek web design
st.markdown("""
<style>
    /* Global styling */
    .stApp {
        background-color: #000000;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1 {
        color: #f97316 !important;
        font-weight: 800 !important;
        letter-spacing: -1px;
    }
    h2, h3 {
        color: #cbd5e1 !important;
    }
    
    /* Input fields & Uploader */
    .stTextInput input, .stFileUploader {
        background-color: #111111 !important;
        border: 1px solid #333333 !important;
        color: #f8fafc !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #f97316 !important;
        box-shadow: 0 0 0 1px #f97316 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #f97316, #ea580c) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.4) !important;
    }
    
    /* Cards for captions */
    .caption-card {
        background-color: #111111;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        transition: transform 0.2s;
    }
    .caption-card:hover {
        transform: translateY(-2px);
        border-color: #f97316;
    }
    .caption-title {
        color: #f97316;
        font-size: 0.875rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .caption-text {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎬 Nami")
st.markdown("### AI-Powered Video Captioning Agent")
st.markdown("Transform your video content into engaging captions across multiple styles instantly.")

# Import backend logic safely
try:
    from app.services.caption_engine import generate_captions
    from app.config import settings
    import tempfile
    import os
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
    video_url = st.text_input("Video URL", placeholder="Paste a public MP4 link or YouTube URL here...")

with tab2:
    uploaded_file = st.file_uploader("Upload a video", type=["mp4", "mov", "avi", "webm"])

generate_btn = st.button("Generate Captions ✨", use_container_width=True)

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
        with st.spinner("Processing video and generating AI captions..."):
            try:
                start_time = time.time()
                
                # generate_captions expects a string URL/path
                captions = generate_captions(source_to_process, ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"])
                
                elapsed = time.time() - start_time
                
                st.success(f"Captions generated successfully in {elapsed:.1f} seconds!")
                
                # Display results in beautiful cards
                styles = {
                    "formal": ("👔 Formal", captions.get("formal", "")),
                    "sarcastic": ("😏 Sarcastic", captions.get("sarcastic", "")),
                    "humorous_tech": ("💻 Tech Humor", captions.get("humorous_tech", "")),
                    "humorous_non_tech": ("😂 Casual Humor", captions.get("humorous_non_tech", ""))
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
st.caption("Powered by Fireworks AI (MiniMax) • Built for AMD Hackathon")
