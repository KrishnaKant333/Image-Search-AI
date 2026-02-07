/**
 * Natural Language Image Search - Frontend JavaScript
 * Handles file uploads, search, and UI interactions
 */

// ===== DOM Elements =====
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const getStartedBtn = document.getElementById('getStartedBtn');
const uploadSection = document.querySelector('.upload-section');
const resultsSection = document.querySelector('.results-section');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const resultsGrid = document.getElementById('resultsGrid');
const resultsTitle = document.getElementById('resultsTitle');
const resultsCount = document.getElementById('resultsCount');
const emptyState = document.getElementById('emptyState');
const imageModal = document.getElementById('imageModal');
const modalImage = document.getElementById('modalImage');
const modalInfo = document.getElementById('modalInfo');
const modalClose = document.getElementById('modalClose');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');

// ===== State =====
let currentImages = [];

// ===== Utility Functions =====

/** 
 * Show toast notification
 */
function showToast(message, type = 'info') {
    toastMessage.textContent = message;
    toast.className = 'toast show ' + type;

    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

async function compressImage(file) {
    // Skip compression for small files (keeps full quality for docs/screenshots)
    if (file.size < 500 * 1024) return file;

    const img = await createImageBitmap(file);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // OCR-friendly: keep higher resolution so text stays readable (max 2048 on longest side)
    const MAX = 2048;
    const scale = Math.min(1, MAX / Math.max(img.width, img.height));

    canvas.width = Math.round(img.width * scale);
    canvas.height = Math.round(img.height * scale);

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // High-quality JPEG (0.92) to preserve sharp text edges for OCR; 0.75 caused artifacts
    return new Promise((resolve) => {
        canvas.toBlob(
            (blob) => {
                resolve(new File([blob], file.name, {
                    type: "image/jpeg"
                }));
            },
            "image/jpeg",
            0.92
        );
    });
}


// ===== Upload Functions =====

/**
 * Handle file upload
 */
async function uploadFiles(files) {
    if (!files || files.length === 0) return;

    // Filter valid image files
    const validFiles = Array.from(files).filter(file =>
        file.type.startsWith('image/')
    );

    if (validFiles.length === 0) {
        showToast('Please select valid image files', 'error');
        return;
    }

    // Show progress
    uploadProgress.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = `Optimizing & processing ${validFiles.length} image(s)...`;


    // Create form data
    const formData = new FormData();

    for (const file of validFiles) {
        const compressedFile = await compressImage(file);
        formData.append('files', compressedFile);
    }

    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 5;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
            }
        }, 200);

        // Upload files
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        clearInterval(progressInterval);
        progressFill.style.width = '100%';

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const result = await response.json();

        // Show results
        if (result.uploaded.length > 0) {
            showToast(`Successfully uploaded ${result.uploaded.length} image(s)`, 'success');
            progressText.textContent = 'AI processing complete!';

            // Refresh the image list
            loadImages();
        }

        if (result.errors.length > 0) {
            console.error('Upload errors:', result.errors);
            showToast(`${result.errors.length} file(s) failed to upload`, 'error');
        }

    } catch (error) {
        console.error('Upload error:', error);
        showToast('Upload failed. Please try again.', 'error');
    } finally {
        // Hide progress after a delay
        setTimeout(() => {
            uploadProgress.style.display = 'none';
            progressFill.style.width = '0%';
        }, 1500);
    }
}

// ===== Search Functions =====

/**
 * Search images with query
 */
async function searchImages(query = '') {
    try {
        const url = query
            ? `/api/search?q=${encodeURIComponent(query)}`
            : '/api/images';

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error('Search failed');
        }

        const result = await response.json();

        // Update UI
        if (query) {
            resultsTitle.textContent = `Results for "${query}"`;
            currentImages = result.results || [];
        } else {
            resultsTitle.textContent = 'Your Images';
            currentImages = result.images || [];
        }

        resultsCount.textContent = `${currentImages.length} image(s)`;
        renderImages(currentImages, !!query);

        // Auto-scroll to results if searching
        if (query && currentImages.length > 0) {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

    } catch (error) {
        console.error('Search error:', error);
        showToast('Search failed. Please try again.', 'error');
    }
}

/**
 * Load all images
 */
async function loadImages() {
    await searchImages('');
}

/**
 * Search with a hint tag
 */
function searchWithHint(hint) {
    searchInput.value = hint;
    searchImages(hint);
}

// Make it global for onclick handlers
window.searchWithHint = searchWithHint;

// ===== Render Functions =====

/**
 * Render image cards
 */
function renderImages(images, showRelevance = false) {
    if (!images || images.length === 0) {
        resultsGrid.innerHTML = `
            <div class="empty-state" id="emptyState">
                <div class="empty-icon">📷</div>
                <h3>No images found</h3>
                <p>${showRelevance ? 'Try a different search query' : 'Upload some images to get started'}</p>
            </div>
        `;
        return;
    }

    resultsGrid.innerHTML = images.map(img => `
        <div class="image-card" data-testid="card-image-${img.id}" onclick="openImage('${img.id}')">
            ${showRelevance && img.relevance ? `<span class="relevance-badge">${img.relevance} pts</span>` : ''}
            <button class="delete-btn" onclick="event.stopPropagation(); deleteImage('${img.id}')" data-testid="button-delete-${img.id}">&times;</button>
            <img src="/uploads/${escapeHtml(img.filename)}" alt="${escapeHtml(img.original_filename)}" loading="lazy">
            <div class="image-card-info">
                <div class="image-card-name">${escapeHtml(img.original_filename)}</div>
                <div class="image-card-tags">
                ${(img.keywords || []).slice(0, 2).map(keyword =>
                    `<span class="image-tag keyword">${escapeHtml(keyword)}</span>`
                ).join('')}
                ${img.image_type
                ? `<span class="image-tag type">${escapeHtml(img.image_type)}</span>`
                : ''
                }

                ${(img.colors || []).slice(0, 2).map(color =>
                `<span class="image-tag color">${escapeHtml(color)}</span>`
                ).join('')}

                </div>
            </div>
        </div>
    `).join('');
}

// ===== Image Actions =====

/**
 * Open image in modal
 */
function openImage(imageId) {
    const image = currentImages.find(img => img.id === imageId);
    if (!image) return;

    modalImage.src = `/uploads/${image.filename}`;
    modalImage.alt = image.original_filename;

    modalInfo.innerHTML = `
        <div style="color: var(--text-primary); margin-bottom: 8px;">
            <strong>${escapeHtml(image.original_filename)}</strong>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        ${(image.keywords || []).slice(0,2).map(k =>
            `<span class="image-tag keyword">${escapeHtml(k)}</span>`
        ).join('')}
        ${image.image_type ? `<span class="image-tag type">${escapeHtml(image.image_type)}</span>` : ''}

        ${(image.colors || []).slice(0,2).map(c =>
            `<span class="image-tag color">${escapeHtml(c)}</span>`
        ).join('')}
      
        </div>
    `;

    imageModal.classList.add('active');
}

// Make it global for onclick handlers
window.openImage = openImage;

/**
 * Delete an image
 */
async function deleteImage(imageId) {
    if (!confirm('Are you sure you want to delete this image?')) {
        return;
    }

    try {
        const response = await fetch(`/api/images/${imageId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showToast('Image deleted', 'success');
            loadImages();
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Failed to delete image', 'error');
    }
}

// Make it global for onclick handlers
window.deleteImage = deleteImage;

// ===== Event Listeners =====

// File input change
fileInput.addEventListener('change', (e) => {
    uploadFiles(e.target.files);
    fileInput.value = ''; // Reset for same file re-upload
});

// Drag and drop
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    uploadFiles(e.dataTransfer.files);
});

// Search
searchBtn.addEventListener('click', () => {
    searchImages(searchInput.value.trim());
});

searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchImages(searchInput.value.trim());
    }
});

// Clear search on empty input
searchInput.addEventListener('input', (e) => {
    if (e.target.value === '') {
        loadImages();
    }
});

// Modal close
modalClose.addEventListener('click', () => {
    imageModal.classList.remove('active');
});

// Get Started Scroll
getStartedBtn.addEventListener('click', () => {
    uploadSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
        imageModal.classList.remove('active');
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        imageModal.classList.remove('active');
    }
});

// ===== Initialize =====
document.addEventListener('DOMContentLoaded', () => {
    loadImages();
});

document.getElementById('clearAllBtn').addEventListener('click', async () => {
    if (!confirm('Delete all uploaded images?')) return;

    const res = await fetch('/api/clear', { method: 'POST' });
    const data = await res.json();

    if (data.success) {
        loadImages(); // reload gallery
        showToast('All images deleted');
    }
});

const scrollTopBtn = document.getElementById('scrollTopBtn');

window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
        scrollTopBtn.style.display = 'block';
    } else {
        scrollTopBtn.style.display = 'none';
    }
});

scrollTopBtn.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});