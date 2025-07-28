// MedRAG - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Check which page we're on
    const currentPath = window.location.pathname;
    
    // Initialize common elements
    initializeCommon();
    
    // Initialize page-specific functionality
    if (currentPath === '/' || currentPath === '/index.html') {
        // Home page
    } else if (currentPath === '/documents' || currentPath.includes('/documents/')) {
        initializeDocumentsPage();
    } else if (currentPath === '/query' || currentPath.includes('/query/')) {
        initializeQueryPage();
    }
});

// Common functionality across all pages
function initializeCommon() {
    // Add active class to current nav item
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.includes(href))) {
            link.classList.add('active');
        }
    });

    // Check API key status for pages that need it
    if (currentPath === '/query' || currentPath === '/documents') {
        checkApiKeyStatus();
    }
}

// Check if API key is configured
function checkApiKeyStatus() {
    const apiKey = sessionStorage.getItem('openai_api_key');
    if (!apiKey) {
        // Show warning banner
        showApiKeyWarning();
    }
}

// Show API key warning banner
function showApiKeyWarning() {
    const existingWarning = document.getElementById('api-key-warning');
    if (existingWarning) return; // Already shown

    const warning = document.createElement('div');
    warning.id = 'api-key-warning';
    warning.className = 'alert alert-warning alert-dismissible fade show';
    warning.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        <strong>OpenAI API Key Required:</strong> Please configure your OpenAI API key on the 
        <a href="/" class="alert-link">home page</a> to use AI features.
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the page
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(warning, container.firstChild);
    }
}

// Documents page functionality
function initializeDocumentsPage() {
    const uploadForm = document.getElementById('upload-form');
    const documentsList = document.getElementById('documents-list');
    const loadingDocuments = document.getElementById('loading-documents');
    const noDocuments = document.getElementById('no-documents');
    const documentSearch = document.getElementById('document-search');
    
    // Load documents list
    loadDocuments();
    
    // Handle document upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            uploadDocument();
        });
    }
    
    // Handle document search
    if (documentSearch) {
        documentSearch.addEventListener('input', function() {
            filterDocuments(this.value);
        });
    }
    
    // Document modal functionality
    initializeDocumentModal();
    
    // Show API key status
    showApiKeyStatus();
}

// Show API key status in documents page
function showApiKeyStatus() {
    const apiKey = sessionStorage.getItem('openai_api_key');
    const statusContainer = document.getElementById('api-status-container');
    
    if (!statusContainer) return;
    
    if (apiKey) {
        statusContainer.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>
                <strong>OpenAI API Key Configured:</strong> AI features are available.
            </div>
        `;
    } else {
        statusContainer.innerHTML = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>OpenAI API Key Required:</strong> 
                <a href="/" class="alert-link">Configure your API key</a> to use AI analysis features.
            </div>
        `;
    }
}

// Query page functionality
function initializeQueryPage() {
    const queryForm = document.getElementById('query-form');
    const resultsCard = document.getElementById('results-card');
    const queryLoading = document.getElementById('query-loading');
    const queryResults = document.getElementById('query-results');
    const queryError = document.getElementById('query-error');
    const copyResultsBtn = document.getElementById('copy-results-btn');
    
    // Load patient filter options
    loadPatientOptions();
    
    // Load query history
    loadQueryHistory();
    
    // Handle query submission
    if (queryForm) {
        queryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitQuery();
        });
    }
    
    // Handle copy results
    if (copyResultsBtn) {
        copyResultsBtn.addEventListener('click', function() {
            copyResultsToClipboard();
        });
    }
}

// Document functions
function loadDocuments() {
    const documentsList = document.getElementById('documents-list');
    const loadingDocuments = document.getElementById('loading-documents');
    const noDocuments = document.getElementById('no-documents');
    
    // Show loading
    if (loadingDocuments) loadingDocuments.classList.remove('d-none');
    if (documentsList) documentsList.innerHTML = '';
    if (noDocuments) noDocuments.classList.add('d-none');
    
    fetch('/api/documents/')
    .then(response => {
        console.log('Documents API response status:', response.status);
        if (!response.ok) {
            throw new Error(`Failed to load documents: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Documents data received:', data);
        if (loadingDocuments) loadingDocuments.classList.add('d-none');
        if (data.length === 0) {
            if (noDocuments) noDocuments.classList.remove('d-none');
            return;
        }
        renderDocumentsList(data);
    })
    .catch(error => {
        console.error('Error loading documents:', error);
        if (loadingDocuments) loadingDocuments.classList.add('d-none');
        if (documentsList) {
            documentsList.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Failed to load documents:</strong> ${error.message}
                    <br><small>Please check if the server is running and try again.</small>
                </div>
            `;
        }
        if (noDocuments) noDocuments.classList.remove('d-none');
    });
}

function renderDocumentsList(documents) {
    const documentsList = document.getElementById('documents-list');
    if (!documentsList) return;
    
    documentsList.innerHTML = '';
    
    documents.forEach(doc => {
        const docElement = document.createElement('div');
        docElement.className = 'document-card card mb-2';
        docElement.setAttribute('data-document-id', doc.document_id);
        
        // Title fallback
        const docTitle = doc.title || doc.original_filename || 'Untitled';
        // Date fallback
        let formattedDate = '-';
        if (doc.uploaded_at || doc.upload_date) {
            const rawDate = doc.uploaded_at || doc.upload_date;
            const uploadDate = new Date(rawDate);
            if (!isNaN(uploadDate.getTime())) {
                formattedDate = uploadDate.toLocaleDateString() + ' ' + uploadDate.toLocaleTimeString();
            }
        }
        
        // Determine icon based on document type
        let iconClass = 'fa-file-medical';
        if (doc.document_type === 'lab_result') iconClass = 'fa-flask';
        else if (doc.document_type === 'radiology') iconClass = 'fa-x-ray';
        else if (doc.document_type === 'prescription') iconClass = 'fa-prescription';
        else if (doc.document_type === 'discharge') iconClass = 'fa-hospital';
        
        docElement.innerHTML = `
            <div class="card-body">
                <div class="d-flex align-items-center">
                    <div class="document-icon me-3">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-0">${docTitle}</h6>
                        <div class="small text-muted">
                            ${doc.patient_id ? 'Patient ID: ' + doc.patient_id : 'No patient ID'} | 
                            Uploaded: ${formattedDate}
                        </div>
                    </div>
                    <div>
                        <span class="badge bg-${doc.processed ? 'success' : 'warning'}">
                            ${doc.processed ? 'Processed' : 'Pending'}
                        </span>
                    </div>
                </div>
            </div>
        `;
        
        docElement.addEventListener('click', function() {
            openDocumentModal(doc.document_id);
        });
        
        documentsList.appendChild(docElement);
    });
}

function filterDocuments(searchTerm) {
    const documentCards = document.querySelectorAll('.document-card');
    searchTerm = searchTerm.toLowerCase();
    
    documentCards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function uploadDocument() {
    const form = document.getElementById('upload-form');
    const progressContainer = document.getElementById('upload-progress-container');
    const progressBar = document.getElementById('upload-progress');
    const successAlert = document.getElementById('upload-success');
    const errorAlert = document.getElementById('upload-error');
    
    // Reset alerts
    successAlert.classList.add('d-none');
    errorAlert.classList.add('d-none');
    
    // Show progress
    progressContainer.classList.remove('d-none');
    progressBar.style.width = '0%';

    // Create FormData
    const formData = new FormData(form);

    // Upload file using fetch API
    fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        return response.json();
    })
    .then(data => {
        progressBar.style.width = '100%';
        successAlert.classList.remove('d-none');
        form.reset();
        setTimeout(() => {
            progressContainer.classList.add('d-none');
            loadDocuments();
        }, 500);
    })
    .catch(error => {
        errorAlert.textContent = 'Error uploading document: ' + (error.message || 'Unknown error');
        errorAlert.classList.remove('d-none');
        progressContainer.classList.add('d-none');
        console.error('Error uploading document:', error);
    });
}


function initializeDocumentModal() {
    const deleteBtn = document.getElementById('delete-document-btn');
    const analyzeBtn = document.getElementById('analyze-document-btn');
    
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const documentId = this.getAttribute('data-document-id');
            if (documentId && confirm('Are you sure you want to delete this document?')) {
                deleteDocument(documentId);
            }
        });
    }
    
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', function() {
            const documentId = this.getAttribute('data-document-id');
            if (documentId) {
                analyzeDocument(documentId);
            }
        });
    }
}

function openDocumentModal(documentId) {
    if (!documentId || documentId === 'undefined') {
        alert('Invalid document selected. Please try again.');
        return;
    }
    const modal = new bootstrap.Modal(document.getElementById('documentModal'));
    const modalLoading = document.getElementById('modal-loading');
    const documentDetails = document.getElementById('document-details');
    const deleteBtn = document.getElementById('delete-document-btn');
    const analyzeBtn = document.getElementById('analyze-document-btn');
    
    // Reset and show modal
    modalLoading.classList.remove('d-none');
    documentDetails.classList.add('d-none');
    if (!documentId || documentId === 'undefined') {
        deleteBtn.disabled = true;
        analyzeBtn.disabled = true;
        document.getElementById('modal-loading').innerHTML = `<div class="alert alert-danger">Invalid document ID. Please refresh the page and try again.</div>`;
        return;
    }
    deleteBtn.disabled = false;
    analyzeBtn.disabled = false;
    deleteBtn.setAttribute('data-document-id', documentId);
    analyzeBtn.setAttribute('data-document-id', documentId);
    modal.show();
    
    // Fetch document details
    fetch(`/api/documents/${documentId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load document details');
            }
            return response.json();
        })
        .then(doc => {
            // Title fallback
            const docTitle = doc.title || doc.original_filename || 'Untitled';
            // Type fallback
            const docType = doc.document_type || 'Unknown';
            // Date fallback
            let formattedDate = '-';
            if (doc.uploaded_at || doc.upload_date) {
                const rawDate = doc.uploaded_at || doc.upload_date;
                const uploadDate = new Date(rawDate);
                if (!isNaN(uploadDate.getTime())) {
                    formattedDate = uploadDate.toLocaleDateString() + ' ' + uploadDate.toLocaleTimeString();
                }
            }
            // File size fallback
            let fileSizeText = 'N/A';
            if (doc.file_size && !isNaN(doc.file_size)) {
                fileSizeText = formatFileSize(doc.file_size);
            }
            // Patient ID fallback
            const patientIdText = doc.patient_id || 'N/A';
            // Status fallback
            const statusText = doc.processed ? 'Processed' : 'Pending';

            // Update modal content
            document.getElementById('documentModalTitle').textContent = docTitle;
            document.getElementById('detail-title').textContent = docTitle;
            document.getElementById('detail-type').textContent = docType;
            document.getElementById('detail-patient-id').textContent = patientIdText;
            document.getElementById('detail-date').textContent = formattedDate;
            document.getElementById('detail-size').textContent = fileSizeText;
            document.getElementById('detail-status').textContent = statusText;
            
            // Show key information if available
            const keyInfoElement = document.getElementById('detail-key-info');
            if (doc.key_information && doc.key_information.length > 0) {
                let keyInfoHtml = '<ul class="mb-0">';
                doc.key_information.forEach(info => {
                    keyInfoHtml += `<li>${info}</li>`;
                });
                keyInfoHtml += '</ul>';
                keyInfoElement.innerHTML = keyInfoHtml;
            } else {
                keyInfoElement.innerHTML = '<p class="text-muted mb-0">No key information extracted yet.</p>';
            }
            
            // Show details and hide loading
            modalLoading.classList.add('d-none');
            documentDetails.classList.remove('d-none');
        })
        .catch(error => {
            console.error('Error loading document details:', error);
            modalLoading.innerHTML = `
                <div class="alert alert-danger">
                    Failed to load document details. Please try again later.
                </div>
            `;
        });
}

function deleteDocument(documentId) {
    if (!documentId || documentId === 'undefined') {
        alert('Invalid document ID. Cannot delete.');
        return;
    }
    fetch(`/api/documents/${documentId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete document');
        }
        // Close modal and reload documents
        const modal = bootstrap.Modal.getInstance(document.getElementById('documentModal'));
        if (modal) modal.hide();
        loadDocuments();
    })
    .catch(error => {
        console.error('Error deleting document:', error);
        alert('Failed to delete document. Please try again later.');
    });
}

function analyzeDocument(documentId) {
    // Check if API key is configured
    const apiKey = sessionStorage.getItem('openai_api_key');
    if (!apiKey) {
        alert('Please configure your OpenAI API key on the home page first.');
        window.location.href = '/';
        return;
    }

    // Redirect to the /query page, passing patient_id if available
    if (!documentId || documentId === 'undefined') {
        alert('Invalid document ID. Cannot analyze.');
        return;
    }
    // Try to get patient_id from the modal (if present)
    const patientIdElem = document.getElementById('detail-patient-id');
    let patientId = '';
    if (patientIdElem && patientIdElem.textContent && patientIdElem.textContent !== 'N/A') {
        patientId = patientIdElem.textContent.trim();
    }
    // Build query string
    let queryUrl = '/query';
    if (patientId) {
        queryUrl += `?patient_id=${encodeURIComponent(patientId)}`;
    }
    window.location.href = queryUrl;
}

// Query functions
function loadPatientOptions() {
    const patientFilter = document.getElementById('patient-filter');
    if (!patientFilter) return;
    
    // Clear existing options
    patientFilter.innerHTML = '';
    // Add default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'All Patients';
    patientFilter.appendChild(defaultOption);
    
    // Fetch patient IDs from backend
    fetch('/api/documents/patients/ids')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load patient list');
            }
            return response.json();
        })
        .then(data => {
            if (data.patient_ids && data.patient_ids.length > 0) {
                data.patient_ids.forEach(pid => {
                    const option = document.createElement('option');
                    option.value = pid;
                    option.textContent = pid;
                    patientFilter.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading patient list:', error);
        });
}


// In-memory recent queries for the session
const recentQueries = [];

function loadQueryHistory() {
    const historyList = document.getElementById('query-history-list');
    const historyLoading = document.getElementById('history-loading');
    const noHistory = document.getElementById('no-history');

    if (!historyList || !historyLoading || !noHistory) {
        return;
    }

    historyLoading.classList.add('d-none');
    historyList.innerHTML = '';

    if (recentQueries.length === 0) {
        noHistory.classList.remove('d-none');
    } else {
        noHistory.classList.add('d-none');
        renderQueryHistory(recentQueries);
    }
}

function renderQueryHistory(historyItems) {
    const historyList = document.getElementById('query-history-list');
    if (!historyList) return;
    historyList.innerHTML = ''; // Clear current items

    historyItems.forEach(item => {
        const queryDate = new Date(item.timestamp);
        const formattedDate = queryDate.toLocaleDateString() + ' ' + queryDate.toLocaleTimeString();

        const listItem = document.createElement('div');
        listItem.className = 'history-item list-group-item list-group-item-action';
        listItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h6 class="mb-1 text-primary query-text">${item.query}</h6>
                <small class="text-muted">${formattedDate}</small>
            </div>
            <small class="text-muted">Patient ID: ${item.patient_id || 'Any'}</small>
        `;
        listItem.addEventListener('click', () => {
            document.getElementById('query-input').value = item.query;
            const patientFilter = document.getElementById('patient-filter');
            if (patientFilter) patientFilter.value = item.patient_id || ''; // Set patient filter if exists
            // Optionally, re-submit query or scroll to top
            document.getElementById('query-form').scrollIntoView({ behavior: 'smooth' });
        });
        historyList.appendChild(listItem);
    });
}

function submitQuery() {
    const queryInput = document.getElementById('query-input');
    const patientFilter = document.getElementById('patient-filter');
    const queryType = document.getElementById('query-type');
    const responseLength = document.getElementById('response-length');
    const resultsCard = document.getElementById('results-card');
    const queryLoading = document.getElementById('query-loading');
    const queryResults = document.getElementById('query-results');
    const queryError = document.getElementById('query-error');
    const resultQuestion = document.getElementById('result-question');
    const resultAnswer = document.getElementById('result-answer');
    const resultSources = document.getElementById('result-sources');
    
    // Validate input
    if (!queryInput.value.trim()) {
        alert('Please enter a question');
        queryInput.focus();
        return;
    }
    
    // Show results card and loading states
    resultsCard.classList.remove('d-none');
    queryLoading.classList.remove('d-none');
    queryResults.classList.add('d-none');
    queryError.classList.add('d-none');

    // Scroll to results card for better UX
    resultsCard.scrollIntoView({ behavior: 'smooth' });

    // Get API key from session storage
    const apiKey = sessionStorage.getItem('openai_api_key');
    if (!apiKey) {
        alert('Please configure your OpenAI API key on the home page first.');
        window.location.href = '/';
        return;
    }

    // Create FormData from the form
    const form = document.getElementById('query-form');
    const formData = new FormData(form);
    formData.append('openai_api_key', apiKey);

    fetch('/api/summaries/query', { // Ensure this is the correct endpoint
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            // Try to parse error from backend if JSON, otherwise use status text
            return response.json()
                .then(errData => { 
                    throw new Error(errData.detail || response.statusText || 'Server error'); 
                })
                .catch(() => { // If error response is not JSON
                    throw new Error(response.statusText || 'Server error');
                });
        }
        return response.json();
    })
    .then(data => {
        queryLoading.classList.add('d-none');
        queryResults.classList.remove('d-none');

        const currentQuery = queryInput.value.trim();
        resultQuestion.textContent = currentQuery;
        // Defensive: always pass a string to formatAnswer
        resultAnswer.innerHTML = formatAnswer(typeof data.summary === 'string' ? data.summary : '');

        resultSources.innerHTML = ''; // Clear previous sources
        if (data.sources && data.sources.length > 0) {
            data.sources.forEach(source => {
                const sourceItem = document.createElement('li');
                sourceItem.className = 'list-group-item source-document';
                const patientIdForModal = source.patient_id || ''; // Ensure a string for dataset
                const relevanceText = source.relevance ? `<span class="badge bg-light text-dark ms-2">Relevance: ${(source.relevance * 100).toFixed(0)}%</span>` : '';
                
                sourceItem.innerHTML = `
                    <a href="#" data-doc-id="${source.id}" data-patient-id="${patientIdForModal}">
                        <i class="fas fa-file-alt me-2"></i>${source.title}
                    </a>
                    ${relevanceText}
                `;
                sourceItem.querySelector('a').addEventListener('click', function(e) {
                    e.preventDefault();
                    openDocumentModal(this.dataset.docId, this.dataset.patientId);
                });
                resultSources.appendChild(sourceItem);
            });
        } else {
            resultSources.innerHTML = '<li class="list-group-item text-muted">No specific source documents cited.</li>';
        }
        // Add to recent queries (prevent duplicates at top)
        if (!(recentQueries[0] && recentQueries[0].query === currentQuery && recentQueries[0].patient_id === patientFilter.value)) {
            recentQueries.unshift({
                query: currentQuery,
                patient_id: patientFilter.value,
                timestamp: new Date().toISOString()
            });
            // Limit to 10 recent queries
            if (recentQueries.length > 10) recentQueries.pop();
        }
        loadQueryHistory(); // Refresh history after successful query
    })
    .catch(error => {
        console.error('Error submitting query:', error);
        queryLoading.classList.add('d-none');
        queryError.classList.remove('d-none');
        queryError.textContent = `Failed to get summary: ${error.message}`;
    });
}

function formatAnswer(text) {
    // Defensive: handle undefined/null or non-string input
    if (!text || typeof text !== 'string') {
        return '<p><em>No answer available.</em></p>';
    }
    // Convert line breaks to paragraphs
    const paragraphs = text.split('\n\n');
    return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

function copyResultsToClipboard() {
    const resultQuestion = document.getElementById('result-question').textContent;
    const resultAnswer = document.getElementById('result-answer').innerText;
    
    const textToCopy = `Question: ${resultQuestion}\n\nAnswer: ${resultAnswer}`;
    
    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            // Show temporary success message
            const copyBtn = document.getElementById('copy-results-btn');
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check me-1"></i>Copied!';
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
            alert('Failed to copy to clipboard');
        });
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
