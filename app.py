"""
Natural Language Image Search Web App
Flask backend with AI-powered image processing and search
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# Import AI modules
from ai.ocr import extract_text
from ai.color import extract_dominant_colors
from ai.vision import classify_image_type, detect_content_keywords, get_image_metadata

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
METADATA_FILE = 'metadata/data.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('metadata', exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_metadata():
    """Load metadata from JSON file"""
    if not os.path.exists(METADATA_FILE):
        return {'images': []}
    try:
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'images': []}


def save_metadata(data):
    """Save metadata to JSON file"""
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def process_image(filepath, filename):
    """
    Process an uploaded image through the AI pipeline.
    Extracts text, colors, and classifies the image type.
    """
    print(f"Processing image: {filename}")
    
    # Extract OCR text
    ocr_text = extract_text(filepath)
    print(f"  OCR text: {ocr_text[:100]}..." if len(ocr_text) > 100 else f"  OCR text: {ocr_text}")
    
    # Extract dominant colors
    colors = extract_dominant_colors(filepath, num_colors=3)
    print(f"  Colors: {colors}")
    
    # Classify image type
    image_type = classify_image_type(filepath)
    print(f"  Type: {image_type}")
    
    # Get image metadata
    metadata = get_image_metadata(filepath)
    
    # Detect content keywords based on OCR and image analysis
    keywords = detect_content_keywords(filepath, ocr_text)
    print(f"  Keywords: {keywords}")
    
    return {
        'ocr_text': ocr_text,
        'colors': colors,
        'image_type': image_type,
        'keywords': keywords,
        'metadata': metadata
    }


def calculate_relevance(image_data, query_terms):
    """
    Calculate relevance score for an image based on query terms.
    Higher score = more relevant.
    """
    score = 0
    query_terms = [term.lower() for term in query_terms]
    
    # Check OCR text (highest weight)
    ocr_text = image_data.get('ocr_text', '').lower()
    for term in query_terms:
        if term in ocr_text:
            score += 10  # Strong match
            # Bonus for exact word match
            if f' {term} ' in f' {ocr_text} ':
                score += 5
    
    # Check colors (medium weight)
    colors = [c.lower() for c in image_data.get('colors', [])]
    for term in query_terms:
        if term in colors:
            score += 7
    
    # Check image type
    image_type = image_data.get('image_type', '').lower()
    for term in query_terms:
        if term in image_type:
            score += 5
    
    # Check keywords
    keywords = [k.lower() for k in image_data.get('keywords', [])]
    for term in query_terms:
        if term in keywords:
            score += 8
        # Partial keyword match
        for keyword in keywords:
            if term in keyword or keyword in term:
                score += 3
    
    # Check filename
    filename = image_data.get('original_filename', '').lower()
    for term in query_terms:
        if term in filename:
            score += 4
    
    return score


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/upload', methods=['POST'])
def upload_images():
    """
    Handle multiple image uploads.
    Processes each image through the AI pipeline.
    """
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    metadata = load_metadata()
    uploaded = []
    errors = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                # Save file
                file.save(filepath)
                
                # Process with AI
                analysis = process_image(filepath, original_filename)
                
                # Create image record
                image_record = {
                    'id': uuid.uuid4().hex,
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'uploaded_at': datetime.now().isoformat(),
                    'ocr_text': analysis['ocr_text'],
                    'colors': analysis['colors'],
                    'image_type': analysis['image_type'],
                    'keywords': analysis['keywords'],
                    'metadata': analysis['metadata']
                }
                
                metadata['images'].append(image_record)
                uploaded.append({
                    'id': image_record['id'],
                    'filename': unique_filename,
                    'original_filename': original_filename
                })
                
            except Exception as e:
                errors.append({'filename': original_filename, 'error': str(e)})
        else:
            errors.append({'filename': file.filename, 'error': 'File type not allowed'})
    
    # Save updated metadata
    save_metadata(metadata)
    
    return jsonify({
        'uploaded': uploaded,
        'errors': errors,
        'total_images': len(metadata['images'])
    })


@app.route('/api/search', methods=['GET'])
def search_images():
    """
    Search images using natural language query.
    Returns images sorted by relevance.
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        # Return all images if no query
        metadata = load_metadata()
        images = metadata.get('images', [])
        return jsonify({
            'query': '',
            'results': [
                {
                    'id': img['id'],
                    'filename': img['filename'],
                    'original_filename': img['original_filename'],
                    'image_type': img.get('image_type', 'other'),
                    'colors': img.get('colors', []),
                    'relevance': 0
                }
                for img in images
            ],
            'total': len(images)
        })
    
    # Split query into search terms
    query_terms = query.lower().split()
    
    # Also add common synonyms/variations
    expanded_terms = set(query_terms)
    
    # Expand common terms
    expansions = {
        'upi': ['payment', 'transaction', 'gpay', 'phonepe', 'paytm'],
        'payment': ['upi', 'transaction', 'paid', 'money'],
        'id': ['identity', 'card', 'student', 'college'],
        'card': ['id', 'identity'],
        'bill': ['invoice', 'receipt', 'payment'],
        'receipt': ['bill', 'invoice'],
        'screenshot': ['screen', 'capture'],
        'photo': ['picture', 'image', 'pic'],
        'doc': ['document', 'paper'],
        'document': ['doc', 'paper', 'file'],
    }
    
    for term in query_terms:
        if term in expansions:
            expanded_terms.update(expansions[term])
    
    metadata = load_metadata()
    images = metadata.get('images', [])
    
    # Calculate relevance for each image
    results = []
    for img in images:
        score = calculate_relevance(img, list(expanded_terms))
        if score > 0:  # Only include images with some relevance
            results.append({
                'id': img['id'],
                'filename': img['filename'],
                'original_filename': img['original_filename'],
                'image_type': img.get('image_type', 'other'),
                'colors': img.get('colors', []),
                'relevance': score
            })
    
    # Sort by relevance (highest first)
    results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return jsonify({
        'query': query,
        'results': results,
        'total': len(results)
    })


@app.route('/api/images', methods=['GET'])
def get_all_images():
    """Get all uploaded images"""
    metadata = load_metadata()
    images = metadata.get('images', [])
    
    return jsonify({
        'images': [
            {
                'id': img['id'],
                'filename': img['filename'],
                'original_filename': img['original_filename'],
                'image_type': img.get('image_type', 'other'),
                'colors': img.get('colors', []),
                'uploaded_at': img.get('uploaded_at', '')
            }
            for img in images
        ],
        'total': len(images)
    })


@app.route('/api/images/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete an image by ID"""
    metadata = load_metadata()
    images = metadata.get('images', [])
    
    # Find and remove the image
    image_to_delete = None
    for i, img in enumerate(images):
        if img['id'] == image_id:
            image_to_delete = images.pop(i)
            break
    
    if not image_to_delete:
        return jsonify({'error': 'Image not found'}), 404
    
    # Delete file from disk
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete['filename'])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Save updated metadata
    save_metadata(metadata)
    
    return '', 204


if __name__ == '__main__':
    # Initialize empty metadata file if it doesn't exist
    if not os.path.exists(METADATA_FILE):
        save_metadata({'images': []})
    
    app.run(host='0.0.0.0', port=5000, debug=False)
