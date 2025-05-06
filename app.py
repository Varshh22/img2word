import streamlit as st
import io
import docx
import base64
import tempfile
import os
import sys
import subprocess

# Check if pytesseract is installed
try:
    import pytesseract
    from PIL import Image
except ImportError:
    st.error("pytesseract or PIL not installed. Install them using: pip install pytesseract pillow")
    st.stop()

# Function to check if tesseract is installed and find its path
def check_tesseract():
    try:
        # Try to get tesseract version
        version = pytesseract.get_tesseract_version()
        return True, f"Tesseract is installed (version: {version})"
    except Exception as e:
        # Try to find tesseract manually
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract'
        ]
        
        for path in possible_paths:
            if os.path.isfile(path):
                return False, f"Tesseract found at {path} but Python can't access it. Try setting path explicitly."
        
        return False, "Tesseract not found in common locations. Please verify your installation."

# Set page configuration
st.set_page_config(
    page_title="Image Text Extractor",
    page_icon="📝",
    layout="centered"
)

# Main title with styling
st.title("📝 Image Text Extractor")
st.markdown("Upload an image to extract text and download as Word document")

# Check if tesseract is installed
tesseract_installed, tesseract_message = check_tesseract()

# Add debug information
with st.expander("Tesseract Status (Debug Info)", expanded=True):
    st.write(tesseract_message)
    
    # Display system info
    st.write(f"**Python Version:** {sys.version}")
    st.write(f"**Operating System:** {sys.platform}")
    
    # For Windows users, try to find Tesseract in PATH
    if sys.platform.startswith('win'):
        path_env = os.environ.get('PATH', '')
        st.write("**Checking PATH for Tesseract:**")
        tesseract_in_path = False
        
        for path_dir in path_env.split(';'):
            if os.path.exists(os.path.join(path_dir, 'tesseract.exe')):
                st.success(f"Found Tesseract in PATH: {os.path.join(path_dir, 'tesseract.exe')}")
                tesseract_in_path = True
        
        if not tesseract_in_path:
            st.error("Tesseract not found in system PATH.")
            
    # Try to execute tesseract command directly
    try:
        result = subprocess.run(['tesseract', '--version'], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0:
            st.success(f"Command line test successful:\n{result.stdout}")
        else:
            st.error(f"Command line test failed with error:\n{result.stderr}")
    except Exception as e:
        st.error(f"Failed to run tesseract command: {str(e)}")
    
    # Show PyTesseract configuration
    st.write(f"**Current PyTesseract Path:** {pytesseract.pytesseract.tesseract_cmd}")
    
    # Allow manual path setting
    custom_path = st.text_input("Set Tesseract Path Manually:", 
                               value=r"C:\Program Files\Tesseract-OCR\tesseract.exe" if sys.platform.startswith('win') else "/usr/bin/tesseract")
    
    if st.button("Use This Path"):
        try:
            pytesseract.pytesseract.tesseract_cmd = custom_path
            # Test if it works
            version = pytesseract.get_tesseract_version()
            st.success(f"Successfully connected to Tesseract (version: {version})")
            tesseract_installed = True
        except Exception as e:
            st.error(f"Failed to use custom path: {str(e)}")

if not tesseract_installed:
    st.error("""
    ⚠️ Tesseract OCR is not installed or not properly configured!
    
    Please install Tesseract OCR:
    
    **For Windows:**
    1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
    2. Install and add to PATH
    3. Restart your application
    
    **For Ubuntu/Debian:**
    ```
    sudo apt update
    sudo apt install tesseract-ocr
    ```
    
    **For macOS:**
    ```
    brew install tesseract
    ```
    
    Check the debug information above for more details.
    """)

# OCR Settings
with st.expander("⚙️ OCR Settings", expanded=False):
    st.markdown("### Configure OCR Settings")
    
    # Tesseract Options
    psm_options = {
        "3": "3 - Fully automatic page segmentation (Default)",
        "4": "4 - Assume a single column of text",
        "6": "6 - Assume a single uniform block of text",
        "7": "7 - Treat image as a single text line",
        "11": "11 - Sparse text with no specific orientation",
        "12": "12 - Dense text with no specific orientation",
        "13": "13 - Raw line with default orientation"
    }
    
    psm = st.selectbox(
        "Page Segmentation Mode",
        options=list(psm_options.keys()),
        format_func=lambda x: psm_options[x],
        index=0
    )
    
    oem_options = {
        "1": "1 - LSTM neural network only",
        "3": "3 - Default: LSTM + legacy engine (best accuracy)"
    }
    
    oem = st.selectbox(
        "OCR Engine Mode",
        options=list(oem_options.keys()),
        format_func=lambda x: oem_options[x],
        index=1
    )
    
    lang_options = {
        "eng": "English",
        "deu": "German",
        "fra": "French",
        "spa": "Spanish",
        "ita": "Italian"
    }
    
    lang = st.selectbox(
        "Language",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=0
    )

# Function to extract text from image
def extract_text_from_image(image, psm, oem, lang):
    try:
        # Configure OCR options
        custom_config = f'--oem {oem} --psm {psm}'
        if lang != "eng":
            custom_config += f' -l {lang}'
            
        # Extract text using tesseract
        text = pytesseract.image_to_string(
            image, 
            config=custom_config
        )
        
        return text
    except Exception as e:
        st.error(f"Error extracting text: {str(e)}")
        st.info("Check the debug information at the top of the page for troubleshooting.")
        return None

# Function to create downloadable Word document
def create_word_doc(text):
    doc = docx.Document()
    doc.add_paragraph(text)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
        doc.save(tmp.name)
        tmp_path = tmp.name
    
    with open(tmp_path, "rb") as file:
        doc_bytes = file.read()
    
    os.unlink(tmp_path)
    return doc_bytes

# File uploader widget
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png", "bmp", "tiff"])

# Display and process image
if uploaded_file is not None:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Uploaded Image")
        image = Image.open(uploaded_file)
        st.image(image, width=300)
    
    # Try to extract text regardless of automatic detection
    with st.spinner("Extracting text... This may take a moment."):
        extracted_text = extract_text_from_image(image, psm, oem, lang)
    
    # Display extracted text
    with col2:
        st.subheader("Extracted Text")
        if extracted_text:
            st.text_area("", value=extracted_text, height=400, label_visibility="hidden")
            
            # Download buttons in a single row
            st.download_button(
                label="📥 Download as Word",
                data=create_word_doc(extracted_text),
                file_name="extracted_text.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            st.download_button(
                label="📝 Download as Text",
                data=extracted_text,
                file_name="extracted_text.txt",
                mime="text/plain"
            )
        else:
            st.warning("No text was extracted from the image. Check the debug information at the top of the page.")

# Simplified instructions section
with st.expander("ℹ️ How to Use This App", expanded=False):
    st.markdown("""
    ### Simple Steps:
    
    1. **Upload an image** containing text
    2. **View the extracted text** in the right panel
    3. **Download** as Word or Text file
    
    ### Tips for Better Results:
    - Use clear, high-resolution images
    - Ensure good contrast between text and background
    - Adjust OCR settings if needed for better recognition
    """)

# Footer
st.markdown("---")
st.markdown("Created with Streamlit and PyTesseract")