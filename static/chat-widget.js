/**
 * Chat Widget JavaScript Module
 * Provides interactive chat functionality for the learning assistant
 */

class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.messageHistory = [];
        this.isTyping = false;
        this.currentSkill = null; // Track current skill context
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadMessageHistory();
        this.setupAutoResize();
    }

    bindEvents() {
        // Toggle chat window
        const toggleBtn = document.getElementById('chat-toggle');
        const closeBtn = document.getElementById('chat-close');
        const chatWindow = document.getElementById('chat-window');
        const chatInput = document.getElementById('chat-input');
        const chatSend = document.getElementById('chat-send');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleChat());
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeChat());
        }

        // Send message events
        if (chatSend) {
            chatSend.addEventListener('click', () => this.sendMessage());
        }

        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            chatInput.addEventListener('input', () => this.updateSendButton());
        }

        // Suggestion buttons
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const suggestion = e.target.getAttribute('data-suggestion');
                if (suggestion) {
                    this.setInputValue(suggestion);
                    this.sendMessage();
                }
            });
        });

        // Close chat when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isOpen && !e.target.closest('.chat-widget')) {
                this.closeChat();
            }
        });

        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.closeChat();
            }
        });

        // Handle skill panel integration
        this.setupSkillPanelIntegration();
    }

    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        const chatWindow = document.getElementById('chat-window');
        const toggleBtn = document.getElementById('chat-toggle');
        
        if (chatWindow) {
            chatWindow.classList.remove('hidden');
            this.isOpen = true;
            
            // Focus input after animation
            setTimeout(() => {
                const input = document.getElementById('chat-input');
                if (input) input.focus();
            }, 300);

            // Hide badge
            this.hideBadge();
        }

        if (toggleBtn) {
            toggleBtn.style.transform = 'rotate(45deg)';
        }
    }

    closeChat() {
        const chatWindow = document.getElementById('chat-window');
        const toggleBtn = document.getElementById('chat-toggle');
        
        if (chatWindow) {
            chatWindow.classList.add('hidden');
            this.isOpen = false;
        }

        if (toggleBtn) {
            toggleBtn.style.transform = 'rotate(0deg)';
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input?.value.trim();
        
        if (!message || this.isTyping) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        input.value = '';
        this.updateSendButton();

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Process message and get AI response
            const response = await this.processMessage(message);
            this.addMessage(response, 'ai');
        } catch (error) {
            console.error('Error processing message:', error);
            this.addMessage('Sorry, I encountered an error. Please try again.', 'ai');
        } finally {
            this.hideTypingIndicator();
        }
    }

    async processMessage(message) {
        console.log('🔍 Processing message:', message);
        console.log('🎯 Routing to handleGeneralQuery');
        return await this.handleGeneralQuery(message);
        
        // Handle different types of queries
        // if (lowerMessage.includes('path') || lowerMessage.includes('route') || lowerMessage.includes('→')) {
        //     return await this.handlePathQuery(message);
        // } else if (lowerMessage.includes('prerequisite') || lowerMessage.includes('requirement')) {
        //     return await this.handlePrerequisiteQuery(message);
        // } else if (lowerMessage.includes('skill') || lowerMessage.includes('learn')) {
        //     return await this.handleSkillQuery(message);
        // } else {
        //     return await this.handleGeneralQuery(message);
        // }
    }

    async handlePathQuery(message) {
        // Extract skill names from message
        const skillNames = this.extractSkillNames(message);
        
        if (skillNames.length >= 2) {
            try {
                const start = skillNames[0];
                const end = skillNames[1];
                
                const response = await fetch(`/api/skill-path?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
                const data = await response.json();
                
                if (data.path && data.path.length > 0) {
                    this.highlightPath(data.path);
                    return this.formatPathResponse(data.path, start, end);
                } else {
                    return `I couldn't find a direct learning path from "${start}" to "${end}". They might not be connected in the current roadmap, or you might need to go through multiple intermediate skills.`;
                }
            } catch (error) {
                console.error('Path query error:', error);
                return 'Sorry, I had trouble finding that learning path. Please make sure the skill names are correct.';
            }
        } else {
            return 'To find a learning path, please specify two skills like "Find path from Python to Machine Learning" or "Python → Machine Learning".';
        }
    }

    async handlePrerequisiteQuery(message) {
        const skillNames = this.extractSkillNames(message);
        
        if (skillNames.length > 0) {
            const skillName = skillNames[0];
            try {
                const response = await fetch(`/api/skill/${encodeURIComponent(skillName)}`);
                const data = await response.json();
                
                if (data.prerequisites && data.prerequisites.length > 0) {
                    return this.formatPrerequisiteResponse(data.prerequisites, skillName);
                } else {
                    return `${skillName} doesn't have specific prerequisites in the current roadmap, or it's a foundational skill.`;
                }
            } catch (error) {
                console.error('Prerequisite query error:', error);
                return `Sorry, I couldn't find information about "${skillName}". Please check if the skill name is correct.`;
            }
        } else {
            return 'Please specify a skill name to find its prerequisites, like "What are the prerequisites for React?"';
        }
    }

    async handleSkillQuery(message) {
        // This is a general skill-related query
        const response = await fetch('/api/skill/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.response || 'I can help you learn about various skills and their relationships. What specific skill would you like to know about?';
        } else {
            return 'I can help you learn about various skills and their relationships. What specific skill would you like to know about?';
        }
    }

    async handleGeneralQuery(message) {
        // For general queries, we can use the existing chat API
        try {
            console.log('📡 Calling /api/general/chat with message:', message);
            // Use a default skill ID for general queries
            const response = await fetch('/api/general/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Received response from API:', data);
                return data.ai_response || this.getDefaultResponse(message);
            } else {
                console.log('❌ API response not ok:', response.status);
                return this.getDefaultResponse(message);
            }
        } catch (error) {
            console.error('General query error:', error);
            return this.getDefaultResponse(message);
        }
    }

    getDefaultResponse(message) {
        const responses = [
            "I'm here to help you navigate your learning journey! You can ask me about learning paths, skill prerequisites, or any questions about the roadmap.",
            "Feel free to ask me about specific skills, learning paths between technologies, or what you should learn next!",
            "I can help you find the best learning path for your goals. Try asking something like 'Find path from Python to Machine Learning' or 'What should I learn after React?'",
            "Ask me about any skill on the roadmap - I can explain prerequisites, suggest next steps, or help you plan your learning journey!"
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }

    extractSkillNames(message) {
        // Simple skill name extraction - can be enhanced
        const skillMappings = {
            'python': 'python',
            'javascript': 'javascript',
            'js': 'javascript',
            'java': 'java',
            'c++': 'cpp',
            'cpp': 'cpp',
            'react': 'react',
            'angular': 'angular',
            'vue': 'vue',
            'nodejs': 'nodejs',
            'node.js': 'nodejs',
            'machine learning': 'machine learning',
            'ml': 'machine learning',
            'ai': 'ai agents',
            'artificial intelligence': 'ai agents',
            'data analyst': 'data analyst',
            'data analysis': 'data analyst',
            'frontend': 'frontend',
            'backend': 'backend',
            'full stack': 'full stack',
            'devops': 'devops',
            'docker': 'docker',
            'kubernetes': 'kubernetes',
            'aws': 'aws',
            'cloud': 'aws'
        };

        const words = message.toLowerCase().split(/\s+/);
        const foundSkills = [];

        // Look for exact matches
        for (const [key, value] of Object.entries(skillMappings)) {
            if (message.toLowerCase().includes(key)) {
                foundSkills.push(value);
            }
        }

        return [...new Set(foundSkills)]; // Remove duplicates
    }

    formatPathResponse(path, start, end) {
        const skillNames = path.map(skillId => this.getSkillNameById(skillId)).filter(Boolean);
        
        if (skillNames.length > 0) {
            return `Here's your learning path from "${start}" to "${end}":\n\n${skillNames.join(' → ')}\n\nI've highlighted this path on the roadmap for you!`;
        } else {
            return `I found a path from "${start}" to "${end}" and highlighted it on the roadmap. The path has ${path.length} skills in total.`;
        }
    }

    formatPrerequisiteResponse(prerequisites, skillName) {
        const prereqNames = prerequisites.map(p => p.name);
        
        if (prereqNames.length > 0) {
            return `Before learning "${skillName}", you should master these prerequisites:\n\n• ${prereqNames.join('\n• ')}\n\nThese skills will give you the foundation needed for "${skillName}".`;
        } else {
            return `${skillName} doesn't have specific prerequisites in the current roadmap.`;
        }
    }

    getSkillNameById(skillId) {
        // This would ideally come from the current graph data
        // For now, we'll use a simple mapping
        const skillMappings = {
            'python': 'Python',
            'javascript': 'JavaScript',
            'java': 'Java',
            'cpp': 'C++',
            'react': 'React',
            'angular': 'Angular',
            'vue': 'Vue.js',
            'nodejs': 'Node.js',
            'machine learning': 'Machine Learning',
            'ai agents': 'AI Agents',
            'data analyst': 'Data Analyst',
            'frontend': 'Frontend Development',
            'backend': 'Backend Development',
            'full stack': 'Full Stack Development',
            'devops': 'DevOps',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'aws': 'AWS'
        };

        return skillMappings[skillId] || skillId;
    }

    highlightPath(pathIds) {
        // Try to highlight the path in the current graph
        if (typeof cy !== 'undefined') {
            // Reset previous highlights
            cy.elements().removeClass('highlighted not-path');
            cy.nodes().unselect();

            // Dim everything by default
            cy.elements().addClass('not-path');

            // Highlight path nodes
            pathIds.forEach(id => {
                const node = cy.getElementById(id);
                if (node) {
                    node.addClass('highlighted');
                    node.removeClass('not-path');
                    node.select();
                }
            });

            // Highlight path edges
            for (let i = 0; i < pathIds.length - 1; i++) {
                const edgeId = `${pathIds[i]}-${pathIds[i + 1]}`;
                const edge = cy.getElementById(edgeId);
                if (edge) {
                    edge.addClass('highlighted');
                    edge.removeClass('not-path');
                }
            }

            // Fit to highlighted elements
            const highlighted = cy.elements('.highlighted');
            if (highlighted && highlighted.length > 0) {
                cy.fit(highlighted, 80);
            }
        }
    }

    addMessage(content, type) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;

        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${type}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageElement.innerHTML = `
            <div class="message-content">${this.formatMessageContent(content)}</div>
            <div class="message-time">${timeString}</div>
        `;

        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Save to history
        this.messageHistory.push({ content, type, timestamp: now });
        this.saveMessageHistory();

        // Show badge if chat is closed
        if (!this.isOpen && type === 'ai') {
            this.showBadge();
        }
    }

    formatMessageContent(content) {
        // Convert line breaks to HTML
        return content.replace(/\n/g, '<br>');
    }

    setInputValue(value) {
        const input = document.getElementById('chat-input');
        if (input) {
            input.value = value;
            this.updateSendButton();
        }
    }

    updateSendButton() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('chat-send');
        
        if (input && sendBtn) {
            const hasText = input.value.trim().length > 0;
            sendBtn.disabled = !hasText || this.isTyping;
        }
    }

    showTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.classList.remove('hidden');
            this.isTyping = true;
            this.updateSendButton();
        }
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.classList.add('hidden');
            this.isTyping = false;
            this.updateSendButton();
        }
    }

    showBadge() {
        const badge = document.getElementById('chat-badge');
        if (badge) {
            badge.style.display = 'flex';
        }
    }

    hideBadge() {
        const badge = document.getElementById('chat-badge');
        if (badge) {
            badge.style.display = 'none';
        }
    }

    setupAutoResize() {
        const input = document.getElementById('chat-input');
        if (input) {
            input.addEventListener('input', () => {
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 120) + 'px';
            });
        }
    }

    setupSkillPanelIntegration() {
        // Listen for skill panel events
        document.addEventListener('skillPanelOpened', (e) => {
            this.currentSkill = e.detail.skillId;
        });

        document.addEventListener('skillPanelClosed', () => {
            this.currentSkill = null;
        });
    }

    saveMessageHistory() {
        try {
            localStorage.setItem('chatWidgetHistory', JSON.stringify(this.messageHistory.slice(-50))); // Keep last 50 messages
        } catch (error) {
            console.warn('Could not save chat history:', error);
        }
    }

    loadMessageHistory() {
        try {
            const saved = localStorage.getItem('chatWidgetHistory');
            if (saved) {
                this.messageHistory = JSON.parse(saved);
            }
        } catch (error) {
            console.warn('Could not load chat history:', error);
        }
    }

    // Public API methods
    setSkillContext(skillId) {
        this.currentSkill = skillId;
    }

    clearHistory() {
        this.messageHistory = [];
        const messagesContainer = document.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="chat-message ai welcome-message">
                    <div class="message-content">
                        👋 Hi! I'm your Learning Assistant. I can help you:
                        <ul>
                            <li>Find learning paths between skills</li>
                            <li>Explain skill relationships</li>
                            <li>Suggest next steps in your learning journey</li>
                            <li>Answer questions about the roadmap</li>
                        </ul>
                        What would you like to know?
                    </div>
                    <div class="message-time">Just now</div>
                </div>
            `;
        }
        this.saveMessageHistory();
    }
}

// Initialize chat widget when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatWidget = new ChatWidget();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatWidget;
}
