import streamlit as st
from PIL import Image
import io
from datetime import datetime
import zipfile

def setup_page():
    st.set_page_config(
        page_title="Image Compressor Pro",
        page_icon="🖼️",
        layout="centered"
    )
    
    st.markdown("""
        <style>
        .main { padding: 1rem; }
        .stApp { background-color: #f8f9fa; }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.3rem;
            border: none;
            width: 100%;
            margin-top: 1rem;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        </style>
    """, unsafe_allow_html=True)

def compress_image(image, original_size_kb):
    # Convert to RGB if needed
    if image.mode in ('RGBA', 'P'):
        img = image.convert('RGB')
    else:
        img = image.copy()
    
    # Target size calculation (always smaller than original)
    if original_size_kb <= 50:
        target_size_kb = original_size_kb * 1.0  # no reduction for small images
    elif original_size_kb <= 100:
        target_size_kb = original_size_kb * 0.6  # 50% reduction for medium images
    elif original_size_kb <= 500:
        target_size_kb = original_size_kb * 0.2  # 80% reduction for large images
    else:
        target_size_kb = original_size_kb * 0.1  # 90% reduction for very large images
    
    # Binary search for optimal quality
    min_quality = 20
    max_quality = 85
    best_quality = max_quality
    best_output = None
    best_size = float('inf')
    
    while min_quality <= max_quality:
        quality = (min_quality + max_quality) // 2
        output = io.BytesIO()
        
        img.save(output, 
                format='JPEG',
                quality=quality,
                optimize=True,
                progressive=True)
        
        current_size = len(output.getvalue()) / 1024
        
        if current_size <= target_size_kb:
            if current_size > best_size * 0.95:  # Allow slightly larger size if quality is better
                best_output = output.getvalue()
                best_size = current_size
                best_quality = quality
            min_quality = quality + 1
        else:
            max_quality = quality - 1
    
    # If we couldn't achieve target size, use the smallest size we got
    if not best_output:
        output = io.BytesIO()
        img.save(output,
                format='JPEG',
                quality=min_quality,
                optimize=True,
                progressive=True)
        best_output = output.getvalue()
    
    return best_output

def main():
    setup_page()
    
    st.title("🖼️ Prachin Bangla Image Compressor Without Watermark")
    st.markdown("### V2")
    
    mode = st.radio("Processing Mode", ["Single Image", "Multiple Images"], horizontal=True)
    
    if mode == "Single Image":
        uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg', 'webp'])
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            original_size = uploaded_file.size / 1024
            
            st.subheader("Original Image")
            st.image(image, use_column_width=True)
            st.write(f"Original Size: {original_size:.1f} KB")
            
            if st.button("🔄 Compress Image", type="primary"):
                try:
                    with st.spinner("Compressing image..."):
                        compressed_bytes = compress_image(image, original_size)
                        
                        st.subheader("Compressed Result")
                        st.image(compressed_bytes, use_column_width=True)
                        
                        compressed_size = len(compressed_bytes) / 1024
                        reduction = ((original_size - compressed_size) / original_size) * 100
                        
                        st.success(f"✨ Size reduced by {reduction:.1f}% ({original_size:.1f}KB → {compressed_size:.1f}KB)")
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            label="⬇️ Download Compressed Image",
                            data=compressed_bytes,
                            file_name=f"{timestamp}_{uploaded_file.name}",
                            mime="image/jpeg"
                        )
                except Exception as e:
                    st.error(f"Error during compression: {str(e)}")
    
    else:
        uploaded_files = st.file_uploader(
            "Upload Multiple Images",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button("🔄 Compress All Images", type="primary"):
                try:
                    with st.spinner("Processing images..."):
                        compressed_images = []
                        for uploaded_file in uploaded_files:
                            image = Image.open(uploaded_file)
                            original_size = uploaded_file.size / 1024
                            compressed = compress_image(image, original_size)
                            compressed_images.append((uploaded_file.name, compressed))
                        
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            for filename, data in compressed_images:
                                zip_file.writestr(f"compressed_{filename}", data)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        st.download_button(
                            label=f"⬇️ Download All Compressed Images ({len(compressed_images)} files)",
                            data=zip_buffer.getvalue(),
                            file_name=f"{timestamp}.zip",
                            mime="application/zip"
                        )
                        
                        st.subheader("Preview")
                        for filename, compressed_data in compressed_images:
                            col1, col2 = st.columns(2)
                            with col1:
                                original = next(f for f in uploaded_files if f.name == filename)
                                st.image(Image.open(original), caption=f"Original: {filename}")
                            with col2:
                                st.image(Image.open(io.BytesIO(compressed_data)), caption=f"Compressed: {filename}")
                except Exception as e:
                    st.error(f"Error processing images: {str(e)}")
    
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>© Jony Image Compressor for Prachin Bangla.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
