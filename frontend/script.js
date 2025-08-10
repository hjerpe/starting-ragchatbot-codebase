// API base URL - use relative path to work from any host
const API_URL = '/api';

// Global state
let currentSessionId = null;

// Retry configuration
const RETRY_CONFIG = {
    maxRetries: 3,
    baseDelay: 1000, // 1 second
    maxDelay: 5000   // 5 seconds
};

// Utility function for exponential backoff retry
async function retryWithBackoff(fn, retries = RETRY_CONFIG.maxRetries) {
    try {
        return await fn();
    } catch (error) {
        if (retries <= 0) {
            throw error;
        }

        // Calculate delay with exponential backoff
        const delay = Math.min(
            RETRY_CONFIG.baseDelay * Math.pow(2, RETRY_CONFIG.maxRetries - retries),
            RETRY_CONFIG.maxDelay
        );

        // Only retry on network errors or 500s, not on 4xx errors
        if (error.message.includes('network') ||
            error.message.includes('fetch') ||
            error.message.includes('500') ||
            error.message.includes('timeout')) {

            console.log(`Retrying in ${delay}ms... (${retries - 1} retries left)`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return retryWithBackoff(fn, retries - 1);
        }

        throw error;
    }
}

// DOM elements
let chatMessages, chatInput, sendButton, totalCourses, courseTitles, newChatButton, themeToggle;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Get DOM elements after page loads
    chatMessages = document.getElementById('chatMessages');
    chatInput = document.getElementById('chatInput');
    sendButton = document.getElementById('sendButton');
    totalCourses = document.getElementById('totalCourses');
    courseTitles = document.getElementById('courseTitles');
    newChatButton = document.getElementById('newChatButton');
    themeToggle = document.getElementById('themeToggle');

    initializeTheme();
    setupEventListeners();
    createNewSession();
    loadCourseStats();
});

// Event Listeners
function setupEventListeners() {
    // Chat functionality
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    // New chat button
    if (newChatButton) {
        newChatButton.addEventListener('click', startNewChat);
        console.log('New chat button event listener added');
    } else {
        console.error('New chat button not found');
    }

    // Theme toggle
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        themeToggle.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleTheme();
            }
        });
    }

    // Suggested questions
    document.querySelectorAll('.suggested-item').forEach(button => {
        button.addEventListener('click', (e) => {
            const question = e.target.getAttribute('data-question');
            chatInput.value = question;
            sendMessage();
        });
    });
}


// Chat Functions
async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;

    // Disable input and buttons
    chatInput.value = '';
    chatInput.disabled = true;
    sendButton.disabled = true;
    newChatButton.disabled = true;

    // Add user message
    addMessage(query, 'user');

    // Add loading message - create a unique container for it
    const loadingMessage = createLoadingMessage();
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await retryWithBackoff(async () => {
            const response = await fetch(`${API_URL}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    session_id: currentSessionId
                })
            });

            if (!response.ok) {
                let errorMessage = 'Request failed';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
                } catch {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            return response;
        });

        const data = await response.json();

        // Update session ID if new
        if (!currentSessionId) {
            currentSessionId = data.session_id;
        }

        // Replace loading message with response
        loadingMessage.remove();
        addMessage(data.answer, 'assistant', data.sources);

    } catch (error) {
        // Replace loading message with error
        loadingMessage.remove();

        let displayMessage = `Error: ${error.message}`;

        // Provide helpful context for common issues
        if (error.message.includes('API key') || error.message.includes('Invalid key') || error.message.includes('authentication')) {
            displayMessage += '\n\n💡 **Tip**: Please check that a valid Anthropic API key is configured in the server environment.';
        } else if (error.message.includes('connection') || error.message.includes('network') || error.message.includes('fetch')) {
            displayMessage += '\n\n💡 **Tip**: Please check your internet connection and try again.';
        } else if (error.message.includes('rate limit') || error.message.includes('too many requests')) {
            displayMessage += '\n\n💡 **Tip**: Too many requests. Please wait a moment and try again.';
        } else if (error.message.includes('timeout')) {
            displayMessage += '\n\n💡 **Tip**: Request timed out. The server might be busy - please try again.';
        } else if (error.message.includes('500')) {
            displayMessage += '\n\n💡 **Tip**: Server error occurred. Please try again or contact support if the issue persists.';
        } else if (error.message.includes('404')) {
            displayMessage += '\n\n💡 **Tip**: Service endpoint not found. Please check the server configuration.';
        }

        addMessage(displayMessage, 'assistant');
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        newChatButton.disabled = false;
        chatInput.focus();
    }
}

function createLoadingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="loading">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    return messageDiv;
}

function addMessage(content, type, sources = null, isWelcome = false) {
    const messageId = Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}${isWelcome ? ' welcome-message' : ''}`;
    messageDiv.id = `message-${messageId}`;

    // Convert markdown to HTML for assistant messages
    const displayContent = type === 'assistant' ? marked.parse(content) : escapeHtml(content);

    let html = `<div class="message-content">${displayContent}</div>`;

    if (sources && sources.length > 0) {
        // Create clickable links for sources
        const sourceLinks = sources.map(source => {
            if (source.link) {
                return `<a href="${escapeHtml(source.link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.title)}</a>`;
            } else {
                return escapeHtml(source.title);
            }
        });

        html += `
            <details class="sources-collapsible">
                <summary class="sources-header">Sources</summary>
                <div class="sources-content">${sourceLinks.join(', ')}</div>
            </details>
        `;
    }

    messageDiv.innerHTML = html;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return messageId;
}

// Helper function to escape HTML for user messages
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Removed removeMessage function - no longer needed since we handle loading differently

async function createNewSession() {
    currentSessionId = null;
    chatMessages.innerHTML = '';
    addMessage('Welcome to the Course Materials Assistant! I can help you with questions about courses, lessons and specific content. What would you like to know?', 'assistant', null, true);
}

async function startNewChat() {
    console.log('startNewChat function called');

    // Disable button during operation
    newChatButton.disabled = true;

    // Brief visual feedback
    const originalText = newChatButton.innerHTML;
    newChatButton.innerHTML = '<span class="new-chat-icon">●</span><span class="new-chat-text">STARTING...</span>';

    // Clear current session and start new one
    await createNewSession();
    console.log('New session created');

    // Re-enable button and restore original text
    setTimeout(() => {
        newChatButton.innerHTML = originalText;
        newChatButton.disabled = false;

        // Focus on input for immediate use
        chatInput.focus();
        console.log('New chat completed');
    }, 300);
}

// Load course statistics
async function loadCourseStats() {
    try {
        console.log('Loading course stats...');
        const response = await retryWithBackoff(async () => {
            const response = await fetch(`${API_URL}/courses`);
            if (!response.ok) {
                let errorMessage = 'Failed to load course stats';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
                } catch {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }
            return response;
        });

        const data = await response.json();
        console.log('Course data received:', data);

        // Update stats in UI
        if (totalCourses) {
            totalCourses.textContent = data.total_courses;
        }

        // Update course titles
        if (courseTitles) {
            if (data.course_titles && data.course_titles.length > 0) {
                courseTitles.innerHTML = data.course_titles
                    .map(title => `<div class="course-title-item">${title}</div>`)
                    .join('');
            } else {
                courseTitles.innerHTML = '<span class="no-courses">No courses available</span>';
            }
        }

    } catch (error) {
        console.error('Error loading course stats:', error);
        // Set default values on error
        if (totalCourses) {
            totalCourses.textContent = '0';
        }
        if (courseTitles) {
            let errorDisplay = 'Failed to load courses';
            if (error.message.includes('500')) {
                errorDisplay = 'Server error - courses unavailable';
            } else if (error.message.includes('404')) {
                errorDisplay = 'Course service not found';
            } else if (error.message.includes('network') || error.message.includes('fetch')) {
                errorDisplay = 'Network error - courses unavailable';
            }
            courseTitles.innerHTML = `<span class="error">${errorDisplay}</span>`;
        }
    }
}

// Theme Functions
function initializeTheme() {
    // Check if user has a saved theme preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    // Use saved theme, or default to system preference (with dark as fallback)
    const initialTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

    setTheme(initialTheme);

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Only auto-switch if user hasn't manually set a preference
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);

    // Save user preference
    localStorage.setItem('theme', newTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);

    if (themeToggle) {
        const isLight = theme === 'light';
        themeToggle.setAttribute('aria-pressed', isLight.toString());
        themeToggle.setAttribute('aria-label', `Switch to ${isLight ? 'dark' : 'light'} theme`);
        themeToggle.title = `Switch to ${isLight ? 'dark' : 'light'} theme`;
    }
}
