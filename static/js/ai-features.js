/**
 * AI Features JavaScript
 * Enhances the AI functionality of the restaurant website
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AI features
    initAIFeatures();
});

/**
 * Initialize all AI features
 */
function initAIFeatures() {
    // Initialize recommendation system
    initRecommendationSystem();
    
    // Initialize chatbot
    initChatbot();
    
    // Initialize voice recognition
    initVoiceRecognition();
    
    // Initialize food analysis
    initFoodAnalysis();
    
    // Track user interactions for AI learning
    initInteractionTracking();
}

/**
 * Initialize the recommendation system
 */
function initRecommendationSystem() {
    const recommendationContainers = document.querySelectorAll('.ai-recommendation-container');
    if (recommendationContainers.length === 0) return;
    
    // Add hover effects to recommendation cards
    const recommendationCards = document.querySelectorAll('.ai-recommendation-card');
    recommendationCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 5px 15px rgba(0,0,0,0.05)';
        });
        
        // Track recommendation clicks
        card.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            if (itemId) {
                trackInteraction(itemId, 'recommend_click');
            }
        });
    });
}

/**
 * Initialize the chatbot
 */
function initChatbot() {
    // Chatbot initialization is handled in the chatbot.html template
    
    // Add floating chatbot button if it exists
    const chatbotButton = document.getElementById('floating-chatbot-button');
    if (!chatbotButton) return;
    
    chatbotButton.addEventListener('click', function() {
        const chatbotContainer = document.getElementById('floating-chatbot-container');
        if (chatbotContainer) {
            chatbotContainer.classList.toggle('show');
            if (chatbotContainer.classList.contains('show')) {
                this.innerHTML = '<i class="fa fa-times"></i>';
            } else {
                this.innerHTML = '<i class="fa fa-comment"></i>';
            }
        }
    });
}

/**
 * Initialize voice recognition
 */
function initVoiceRecognition() {
    // Voice recognition initialization is handled in the voice_order.html template
}

/**
 * Initialize food analysis
 */
function initFoodAnalysis() {
    // Add interactive elements to food analysis page
    const colorSwatches = document.querySelectorAll('.color-swatch');
    if (colorSwatches.length === 0) return;
    
    colorSwatches.forEach(swatch => {
        swatch.addEventListener('click', function() {
            const color = this.style.backgroundColor;
            const colorName = this.dataset.colorName || 'Selected color';
            
            // Show a tooltip with the color information
            const tooltip = document.createElement('div');
            tooltip.className = 'color-tooltip';
            tooltip.innerHTML = `<span>${colorName}</span>`;
            tooltip.style.backgroundColor = color;
            tooltip.style.color = getContrastColor(color);
            
            document.body.appendChild(tooltip);
            
            // Position the tooltip
            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
            tooltip.style.left = `${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px`;
            
            // Remove the tooltip after a delay
            setTimeout(() => {
                document.body.removeChild(tooltip);
            }, 2000);
        });
    });
}

/**
 * Initialize interaction tracking
 */
function initInteractionTracking() {
    // Track menu item views
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        const itemId = item.dataset.itemId;
        if (itemId) {
            // Track view after a short delay to ensure it's an intentional view
            let viewTimeout;
            
            item.addEventListener('mouseenter', function() {
                viewTimeout = setTimeout(() => {
                    trackInteraction(itemId, 'view');
                }, 1000); // 1 second delay
            });
            
            item.addEventListener('mouseleave', function() {
                clearTimeout(viewTimeout);
            });
            
            // Track clicks
            item.addEventListener('click', function() {
                trackInteraction(itemId, 'view', { 'action': 'click' });
            });
        }
    });
}

/**
 * Track user interaction with a menu item
 * @param {string} itemId - The ID of the menu item
 * @param {string} interactionType - The type of interaction (view, order, favorite, review, recommend_click)
 * @param {object} interactionData - Additional data about the interaction
 */
function trackInteraction(itemId, interactionType, interactionData = {}) {
    // Only track if the user is on a page with AI features
    if (!document.body.classList.contains('ai-features-enabled')) return;
    
    // Send the interaction data to the server
    fetch('/ai/track-interaction/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            item_id: itemId,
            interaction_type: interactionType,
            interaction_data: interactionData
        })
    }).catch(error => {
        console.error('Error tracking interaction:', error);
    });
}

/**
 * Get a contrasting text color (black or white) based on background color
 * @param {string} bgColor - The background color
 * @returns {string} - The contrasting text color
 */
function getContrastColor(bgColor) {
    // Default to black if color parsing fails
    if (!bgColor) return '#000000';
    
    // Convert color to RGB
    let r, g, b;
    
    if (bgColor.startsWith('#')) {
        // Hex color
        const hex = bgColor.substring(1);
        r = parseInt(hex.substring(0, 2), 16);
        g = parseInt(hex.substring(2, 4), 16);
        b = parseInt(hex.substring(4, 6), 16);
    } else if (bgColor.startsWith('rgb')) {
        // RGB color
        const rgbValues = bgColor.match(/\d+/g);
        if (rgbValues && rgbValues.length >= 3) {
            r = parseInt(rgbValues[0]);
            g = parseInt(rgbValues[1]);
            b = parseInt(rgbValues[2]);
        } else {
            return '#000000';
        }
    } else {
        return '#000000';
    }
    
    // Calculate luminance
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
    
    // Return white for dark backgrounds, black for light backgrounds
    return luminance > 0.5 ? '#000000' : '#FFFFFF';
}

/**
 * Get the value of a cookie
 * @param {string} name - The name of the cookie
 * @returns {string} - The cookie value
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
