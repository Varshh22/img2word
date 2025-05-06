import streamlit as st
import pytesseract
from PIL import Image
import docx
import tempfile
import os
import re

# Set up the app
st.set_page_config(page_title="Image Text Extractor", page_icon="📝")
st.title("📝 Image Text Extractor")
st.caption("Upload an image to extract text")

# Function to clean text for Word document
def clean_text(text):
    # Remove non-printable characters except basic punctuation and newlines
    cleaned = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)
    # Replace multiple newlines with single newlines
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    return cleaned.strip()

# Language selection
lang = st.selectbox(
    "Text Language",
    options=["English", "German", "French", "Spanish", "Italian"],
    index=0
)
lang_map = {"English": "eng", "German": "deu", "French": "fra", "Spanish": "spa", "Italian": "ita"}

# File upload
uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Image")
        img = Image.open(uploaded_file)
        st.image(img, width=250)
    
    with col2:
        st.subheader("Extracted Text")
        text = pytesseract.image_to_string(img, lang=lang_map[lang])
        cleaned_text = clean_text(text) if text else ""
        
        if cleaned_text:
            st.text_area("", value=cleaned_text, height=300)
            
            # Single row download buttons
            col_a, col_b = st.columns(2)
            with col_a:
                doc = docx.Document()
                try:
                    doc.add_paragraph(cleaned_text)
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        doc.save(tmp.name)
                        st.download_button(
                            "⬇️ Download as Word",
                            data=open(tmp.name, "rb").read(),
                            file_name="extracted_text.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    os.unlink(tmp.name)
                except Exception as e:
                    st.error("Failed to create Word document")
                    st.error(str(e))
                
            with col_b:
                st.download_button(
                    "⬇️ Download as Text",
                    data=cleaned_text,
                    file_name="extracted_text.txt",
                    mime="text/plain"
                )
        else:
            st.warning("No text found in image")

st.info("💡 Tip: Use clear, high-contrast images for best results")
