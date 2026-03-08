// Rider Chat JavaScript

let currentConversation = null;
let conversations = [];
let lastMessageId = 0; // Track last message to avoid duplicates
let isSendingMessage = false; // Prevent double sending

document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
    setupEventListeners();
});

// Initialize chat
function initializeChat() {
    loadConversations();
    updateStatusText();
}

// Setup event listeners
function setupEventListeners() {
    // Online/Offline status toggle
    const statusToggle = document.getElementById('onlineStatus');
    const statusText = document.getElementById('statusText');
    
    if (statusToggle && statusText) {
        statusToggle.addEventListener('change', function() {
            if (this.checked) {
                statusText.textContent = 'Online';
            } else {
                statusText.textContent = 'Offline';
            }
        });
    }

    // Sidebar profile click
    const sidebarProfile = document.getElementById('sidebarProfile');
    if (sidebarProfile) {
        sidebarProfile.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/rider/profile';
        });
    }

    // Delivery Management toggle
    const deliveryManagementToggle = document.getElementById('deliveryManagementToggle');
    if (deliveryManagementToggle) {
        deliveryManagementToggle.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/rider/pickup';
        });
    }

    // Search input
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', handleSearch);
    }

    // Message input
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
}

// Update status text
function updateStatusText() {
    const statusToggle = document.getElementById('onlineStatus');
    const statusText = document.getElementById('statusText');
    
    if (statusToggle && statusText) {
        if (statusToggle.checked) {
            statusText.textContent = 'Online';
        } else {
            statusText.textContent = 'Offline';
        }
    }
}

// Load conversations
function loadConversations() {
    fetch('/rider/chat/api/conversations')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                conversations = data.conversations;
                displayConversations(conversations);
            } else {
                console.error('Error loading conversations:', data.error);
                displayEmptyConversations();
            }
        })
        .catch(error => {
            console.error('Error fetching conversations:', error);
            displayEmptyConversations();
        });
}

// Display conversations
function displayConversations(convs) {
    const conversationsList = document.getElementById('conversationsList');
    
    if (!conversationsList) return;
    
    if (!convs || convs.length === 0) {
        displayEmptyConversations();
        return;
    }
    
    // Remove duplicates based on delivery_id
    const uniqueConvs = [];
    const seenDeliveryIds = new Set();
    
    convs.forEach(conv => {
        if (!seenDeliveryIds.has(conv.delivery_id)) {
            seenDeliveryIds.add(conv.delivery_id);
            uniqueConvs.push(conv);
        }
    });
    
    // Filter out delivered conversations older than 20 seconds
    const filteredConvs = uniqueConvs.filter(conv => {
        if (conv.delivery_status === 'delivered' && conv.last_message_time) {
            const lastMessageDate = new Date(conv.last_message_time);
            const now = new Date();
            const diffSeconds = (now - lastMessageDate) / 1000;
            return diffSeconds <= 20; // Keep only if 20 seconds or less
        }
        return true; // Keep non-delivered conversations
    });
    
    if (filteredConvs.length === 0) {
        displayEmptyConversations();
        return;
    }
    
    conversationsList.innerHTML = filteredConvs.map(conv => createConversationItem(conv)).join('');
    
    // Add click handlers
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', function() {
            const convId = this.dataset.conversationId;
            const deliveryId = this.dataset.deliveryId;
            selectConversation(convId, parseInt(deliveryId));
        });
    });
}

// Create conversation item HTML
function createConversationItem(conv) {
    const time = formatTime(conv.last_message_time);
    const unreadBadge = conv.unread_count > 0 ? `<span class="unread-badge">${conv.unread_count}</span>` : '';
    
    // Get first letter of contact name for initial
    const initial = conv.contact_name ? conv.contact_name.charAt(0).toUpperCase() : 'U';
    
    // Check if avatar exists and is not default
    const hasAvatar = conv.contact_avatar && 
                     !conv.contact_avatar.includes('default-avatar') && 
                     conv.contact_avatar !== '/static/images/default-avatar.png';
    
    let avatarHTML;
    if (hasAvatar) {
        // Handle both Supabase URLs and local paths
        let avatarSrc;
        if (conv.contact_avatar.startsWith('http://') || conv.contact_avatar.startsWith('https://')) {
            avatarSrc = conv.contact_avatar; // Supabase URL
        } else if (conv.contact_avatar.startsWith('static/')) {
            avatarSrc = `/${conv.contact_avatar}`; // Local with static/ prefix
        } else {
            avatarSrc = `/static/${conv.contact_avatar}`; // Relative path
        }
        avatarHTML = `<img src="${avatarSrc}" alt="${conv.contact_name}">`;
    } else {
        avatarHTML = `<div class="avatar-initial">${initial}</div>`;
    }
    
    return `
        <div class="conversation-item" data-conversation-id="${conv.conversation_id}" data-delivery-id="${conv.delivery_id}">
            <div class="conversation-avatar">
                ${avatarHTML}
            </div>
            <div class="conversation-details">
                <div class="conversation-header">
                    <span class="conversation-name">${conv.contact_name}</span>
                    <span class="conversation-time">${time}</span>
                </div>
                <div class="conversation-message">
                    ${conv.last_message || 'Order #' + conv.order_number}
                    ${unreadBadge}
                </div>
                <div style="font-size: 11px; color: #65676b; margin-top: 2px;">
                    ${conv.seller_shop} • ${conv.delivery_status}
                </div>
            </div>
        </div>
    `;
}

// Display empty conversations
function displayEmptyConversations() {
    const conversationsList = document.getElementById('conversationsList');
    
    if (!conversationsList) return;
    
    conversationsList.innerHTML = `
        <div class="empty-conversations">
            <i class="bi bi-chat-dots"></i>
            <p>No active deliveries</p>
            <p class="empty-subtitle">Accept deliveries to start chatting with buyers</p>
        </div>
    `;
}

// Select conversation
function selectConversation(convId, deliveryId) {
    currentConversation = conversations.find(c => c.conversation_id === convId);
    
    if (!currentConversation) return;
    
    // Reset last message ID when switching conversations
    lastMessageId = 0;
    
    // Update active state
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-conversation-id="${convId}"]`)?.classList.add('active');
    
    // Show chat header and input
    document.getElementById('chatHeader').style.display = 'flex';
    document.getElementById('messageInputContainer').style.display = 'flex';
    
    // Re-enable input by default (will be disabled later if delivered)
    const messageInput = document.getElementById('messageInput');
    const sendBtn = document.getElementById('sendBtn');
    if (messageInput) {
        messageInput.disabled = false;
        messageInput.placeholder = 'Type a message...';
    }
    if (sendBtn) sendBtn.disabled = false;
    
    // Update contact info with proper URL handling
    const contactAvatarDiv = document.querySelector('.contact-avatar');
    const contactAvatarImg = document.getElementById('contactAvatar');
    
    console.log('🖼️ Setting avatar for:', currentConversation.contact_name);
    console.log('📸 Avatar path:', currentConversation.contact_avatar);
    
    // Check if avatar exists and is not default
    const hasAvatar = currentConversation.contact_avatar && 
                     !currentConversation.contact_avatar.includes('default-avatar') && 
                     currentConversation.contact_avatar !== '/static/images/default-avatar.png';
    
    console.log('✅ Has avatar:', hasAvatar);
    
    if (hasAvatar) {
        // Handle both Supabase URLs and local paths
        let avatarSrc;
        if (currentConversation.contact_avatar.startsWith('http://') || currentConversation.contact_avatar.startsWith('https://')) {
            avatarSrc = currentConversation.contact_avatar; // Supabase URL
        } else if (currentConversation.contact_avatar.startsWith('/static/')) {
            avatarSrc = currentConversation.contact_avatar; // Already has /static/ prefix
        } else if (currentConversation.contact_avatar.startsWith('static/')) {
            avatarSrc = `/${currentConversation.contact_avatar}`; // Add leading slash
        } else if (currentConversation.contact_avatar.startsWith('/')) {
            avatarSrc = currentConversation.contact_avatar; // Has leading slash
        } else {
            avatarSrc = `/static/${currentConversation.contact_avatar}`; // Relative path
        }
        
        console.log('🎯 Final avatar src:', avatarSrc);
        contactAvatarImg.src = avatarSrc;
        contactAvatarImg.style.display = 'block';
        
        // Remove any existing initial div
        const existingInitial = contactAvatarDiv.querySelector('.avatar-initial');
        if (existingInitial) existingInitial.remove();
    } else {
        console.log('❌ No avatar, showing initial');
        // Hide image and show initial
        contactAvatarImg.style.display = 'none';
        const initial = currentConversation.contact_name ? currentConversation.contact_name.charAt(0).toUpperCase() : 'U';
        
        // Remove existing initial if any
        const existingInitial = contactAvatarDiv.querySelector('.avatar-initial');
        if (existingInitial) existingInitial.remove();
        
        // Add new initial div
        const initialDiv = document.createElement('div');
        initialDiv.className = 'avatar-initial';
        initialDiv.textContent = initial;
        contactAvatarDiv.appendChild(initialDiv);
    }
    
    document.getElementById('contactName').textContent = currentConversation.contact_name;
    document.getElementById('contactStatus').textContent = `Order #${currentConversation.order_number} • ${currentConversation.delivery_status}`;
    
    // Load messages (initial load)
    loadMessages(deliveryId, true);
}

// Load messages
function loadMessages(deliveryId, isInitialLoad = false) {
    fetch(`/rider/chat/api/messages/${deliveryId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (isInitialLoad) {
                    // First load - display all messages
                    displayMessages(data.messages);
                    if (data.messages.length > 0) {
                        lastMessageId = data.messages[data.messages.length - 1].message_id;
                    }
                } else {
                    // Subsequent loads - only add new messages
                    const newMessages = data.messages.filter(msg => msg.message_id > lastMessageId);
                    if (newMessages.length > 0) {
                        appendNewMessages(newMessages);
                        lastMessageId = newMessages[newMessages.length - 1].message_id;
                    }
                }
            } else {
                console.error('Error loading messages:', data.error);
                if (isInitialLoad) displayEmptyChat();
            }
        })
        .catch(error => {
            console.error('Error fetching messages:', error);
            if (isInitialLoad) displayEmptyChat();
        });
}

// Display messages
function displayMessages(messages) {
    const messagesArea = document.getElementById('messagesArea');
    
    if (!messagesArea) return;
    
    if (messages.length === 0) {
        messagesArea.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666666;">
                <i class="bi bi-chat-text" style="font-size: 48px; margin-bottom: 16px; display: block;"></i>
                <p>No messages yet</p>
                <p style="font-size: 13px; color: #999999; margin-top: 8px;">Start the conversation with the buyer</p>
            </div>
        `;
        return;
    }
    
    messagesArea.innerHTML = messages.map(msg => createMessageBubble(msg)).join('');
    
    // Check if delivery is completed
    if (currentConversation && currentConversation.delivery_status === 'delivered') {
        messagesArea.innerHTML += `
            <div style="text-align: center; padding: 20px; margin: 20px 0;">
                <div style="background: #f0f0f0; padding: 15px; border-radius: 8px; display: inline-block;">
                    <i class="bi bi-check-circle" style="color: #4CAF50; font-size: 24px; margin-bottom: 8px; display: block;"></i>
                    <p style="color: #666666; font-weight: 600; margin: 0;">Order Delivered</p>
                    <p style="color: #999999; font-size: 13px; margin: 5px 0 0 0;">This conversation has ended</p>
                </div>
            </div>
        `;
        
        // Disable message input
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        if (messageInput) messageInput.disabled = true;
        if (sendBtn) sendBtn.disabled = true;
    }
    
    // Scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// Append new messages (for real-time updates)
function appendNewMessages(newMessages) {
    const messagesArea = document.getElementById('messagesArea');
    if (!messagesArea) return;
    
    // Remove empty state if exists
    const emptyState = messagesArea.querySelector('div[style*="text-align: center"]');
    if (emptyState) {
        messagesArea.innerHTML = '';
    }
    
    // Add new messages
    newMessages.forEach(msg => {
        const messageHTML = createMessageBubble(msg);
        messagesArea.insertAdjacentHTML('beforeend', messageHTML);
    });
    
    // Scroll to bottom smoothly
    messagesArea.scrollTo({
        top: messagesArea.scrollHeight,
        behavior: 'smooth'
    });
    
    // Play notification sound (optional)
    playNotificationSound();
}

// Play notification sound for new messages
function playNotificationSound() {
    // Simple beep using Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
        // Silently fail if audio not supported
    }
}

// Create message bubble HTML
function createMessageBubble(msg) {
    const isSent = msg.sender_type === 'rider';
    const messageClass = isSent ? 'sent' : 'received';
    const time = formatMessageTime(msg.created_at); // Use 12-hour format for messages
    
    return `
        <div class="message ${messageClass}">
            <div class="message-bubble">${escapeHtml(msg.message_text)}</div>
            <div class="message-time" data-timestamp="${msg.created_at}">${time}</div>
        </div>
    `;
}

// Send message
function sendMessage() {
    // Prevent double sending
    if (isSendingMessage) {
        console.log('⏳ Already sending a message, please wait...');
        return;
    }
    
    const messageInput = document.getElementById('messageInput');
    
    if (!messageInput || !currentConversation) return;
    
    const messageText = messageInput.value.trim();
    
    if (!messageText) return;
    
    // Set flag to prevent double sending
    isSendingMessage = true;
    console.log('📤 Sending message...');
    
    // Clear input immediately
    messageInput.value = '';
    
    // Add temporary "sending" message with loading animation
    const messagesContainer = document.getElementById('messagesContainer');
    const tempMessageId = 'temp-' + Date.now();
    if (messagesContainer) {
        const tempMessageHTML = `
            <div class="message sent" id="${tempMessageId}">
                <div class="message-bubble">${escapeHtml(messageText)}</div>
                <div class="message-time">
                    <div class="message-sending-indicator">
                        <span class="dot"></span>
                        <span class="dot"></span>
                        <span class="dot"></span>
                    </div>
                </div>
            </div>
        `;
        messagesContainer.insertAdjacentHTML('beforeend', tempMessageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Send to server
    fetch('/rider/chat/api/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            delivery_id: currentConversation.delivery_id,
            message: messageText
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove temporary message
            const tempMsg = document.getElementById(tempMessageId);
            if (tempMsg) tempMsg.remove();
            
            // Add actual message to UI
            addMessageToUI(data.message);
            
            // Update conversation list
            updateConversationLastMessage(currentConversation.conversation_id, messageText);
            
            console.log('✅ Message sent successfully');
        } else {
            // Remove temporary message and show error
            const tempMsg = document.getElementById(tempMessageId);
            if (tempMsg) tempMsg.remove();
            
            console.error('Error sending message:', data.error);
            alert('Failed to send message. Please try again.');
            
            // Restore message text
            messageInput.value = messageText;
        }
    })
    .catch(error => {
        // Remove temporary message and show error
        const tempMsg = document.getElementById(tempMessageId);
        if (tempMsg) tempMsg.remove();
        
        console.error('Error sending message:', error);
        alert('Failed to send message. Please try again.');
        
        // Restore message text
        messageInput.value = messageText;
    })
    .finally(() => {
        // Reset flag after sending (success or failure)
        isSendingMessage = false;
    });
}

// Add message to UI
function addMessageToUI(message) {
    const messagesArea = document.getElementById('messagesArea');
    
    if (!messagesArea) return;
    
    // Remove empty state if exists
    const emptyState = messagesArea.querySelector('div[style*="text-align: center"]');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Add new message
    const messageHTML = createMessageBubble(message);
    messagesArea.insertAdjacentHTML('beforeend', messageHTML);
    
    // Update lastMessageId to prevent duplicate on next load
    if (message.message_id) {
        lastMessageId = message.message_id;
    }
    
    // Scroll to bottom
    messagesArea.scrollTop = messagesArea.scrollHeight;
}

// Update conversation last message
function updateConversationLastMessage(convId, message) {
    const conv = conversations.find(c => c.conversation_id === convId);
    if (conv) {
        conv.last_message = message;
        conv.last_message_time = new Date().toISOString();
    }
    
    // Re-render conversations
    displayConversations(conversations);
}

// Handle search
function handleSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    
    if (!searchTerm) {
        displayConversations(conversations);
        return;
    }
    
    const filtered = conversations.filter(conv => 
        conv.contact_name.toLowerCase().includes(searchTerm) ||
        conv.order_number.toLowerCase().includes(searchTerm) ||
        conv.seller_shop.toLowerCase().includes(searchTerm)
    );
    
    displayConversations(filtered);
}

// Display empty chat
function displayEmptyChat() {
    const messagesArea = document.getElementById('messagesArea');
    
    if (!messagesArea) return;
    
    messagesArea.innerHTML = `
        <div class="empty-chat">
            <i class="bi bi-chat-text"></i>
            <h3>Select a conversation</h3>
            <p>Choose a delivery from the list to start messaging with the buyer</p>
        </div>
    `;
}

// Format time
// Format time for conversation list (relative time)
function formatTime(dateString) {
    if (!dateString) return '';
    
    console.log('🕐 formatTime input:', dateString);
    
    // Parse timestamp directly (format: YYYY-MM-DD HH:MM:SS)
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    console.log('🕐 Date:', date, 'Now:', now, 'Diff (ms):', diff);
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'Just now';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}m`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h`;
    }
    
    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d`;
    }
    
    // More than 7 days
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Format time for message bubbles (12-hour format with AM/PM)
function formatMessageTime(dateString) {
    if (!dateString) return '';
    
    // Parse timestamp directly (format: YYYY-MM-DD HH:MM:SS)
    const date = new Date(dateString);
    
    // Format as 12-hour time with AM/PM (e.g., 3:50 PM)
    let hours = date.getHours();
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12; // Convert to 12-hour format
    
    return `${hours}:${minutes} ${ampm}`;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update message times every second
function updateMessageTimes() {
    const messageTimes = document.querySelectorAll('.message-time');
    messageTimes.forEach(timeElement => {
        const timestamp = timeElement.dataset.timestamp;
        if (timestamp) {
            timeElement.textContent = formatTime(timestamp);
        }
    });
}

// Auto-refresh conversations every 15 seconds (reduced from 5 seconds)
// Only refresh if page is visible to save resources
let conversationRefreshInterval = setInterval(() => {
    if (!document.hidden) {
        loadConversations();
    }
}, 15000);

// Auto-refresh messages every 10 seconds if conversation is open (reduced from 5 seconds)
// Only refresh if page is visible
let messageRefreshInterval = setInterval(() => {
    if (!document.hidden && currentConversation && currentConversation.delivery_id) {
        loadMessages(currentConversation.delivery_id);
    }
}, 10000);

// Update message times every 30 seconds for real-time display (reduced from 10 seconds)
let timeUpdateInterval = setInterval(() => {
    updateMessageTimes();
}, 30000);

// Pause auto-refresh when page is hidden, resume when visible
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('💤 Page hidden - pausing auto-refresh');
    } else {
        console.log('👁️ Page visible - resuming auto-refresh');
        // Immediately refresh when page becomes visible
        loadConversations();
        if (currentConversation && currentConversation.delivery_id) {
            loadMessages(currentConversation.delivery_id);
        }
    }
});
