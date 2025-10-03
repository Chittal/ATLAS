/**
 * Embeddable Skill Panel Component
 * 
 * This component can be embedded in any page to show skill details and chat functionality.
 * 
 * Usage:
 * 1. Include this script in your page
 * 2. Call SkillPanel.show(skillId) to show the panel for a specific skill
 * 3. The panel will appear as a sidebar on the right side of the page
 */

class SkillPanel {
    constructor() {
        this.isVisible = false;
        this.currentSkillId = null;
        this.chatHistory = [];
        this.init();
    }

    init() {
        // Create the panel HTML structure
        this.createPanelHTML();
        this.bindEvents();
    }

    createPanelHTML() {
        const panelHTML = `
            <div id="skill-panel" class="skill-panel hidden">
                <div class="panel-header">
                    <button class="close-btn" onclick="window.skillPanel.close()">&times;</button>
                    <h2 id="skill-name">Skill Name</h2>
                </div>
                
                <div class="panel-content">
                    <div class="skill-description" id="skill-description">
                        Loading skill details...
                    </div>
                    
                    <div class="skill-relations">
                        <div class="prerequisites">
                            <h3>Prerequisites</h3>
                            <ul class="skill-list" id="prerequisites-list">
                                <li class="loading">Loading prerequisites...</li>
                            </ul>
                        </div>
                        
                        <div class="next-skills">
                            <h3>Next Skills</h3>
                            <ul class="skill-list" id="next-skills-list">
                                <li class="loading">Loading next skills...</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="chat-section">
                        <h3>Ask about this skill</h3>
                        <div class="chat-messages" id="chat-messages">
                            <div class="chat-message ai">
                                Hi! I can help you learn about this skill. What would you like to know?
                            </div>
                        </div>
                        <div class="chat-input-container">
                            <input type="text" class="chat-input" id="chat-input" placeholder="Ask a question about this skill..." />
                            <button class="chat-send-btn" id="chat-send-btn">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add to body if not already present
        if (!document.getElementById('skill-panel')) {
            document.body.insertAdjacentHTML('beforeend', panelHTML);
        }
    }

    bindEvents() {
        // Chat input events
        const chatInput = document.getElementById('chat-input');
        const chatSendBtn = document.getElementById('chat-send-btn');

        if (chatInput) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendChatMessage();
                }
            });
        }

        if (chatSendBtn) {
            chatSendBtn.addEventListener('click', () => {
                this.sendChatMessage();
            });
        }
    }

    show(skillId) {
        this.currentSkillId = skillId;
        const panel = document.getElementById('skill-panel');
        if (panel) {
            panel.classList.remove('hidden');
            this.isVisible = true;
            // Reset chat UI when switching/opening a skill
            this.resetChatUI();
            this.loadSkillDetails(skillId);
        }
    }

    close() {
        const panel = document.getElementById('skill-panel');
        if (panel) {
            panel.classList.add('hidden');
            this.isVisible = false;
            this.currentSkillId = null;
            this.chatHistory = [];
        }
    }

    async loadSkillDetails(skillId) {
        try {
            const response = await fetch(`/api/skill/${skillId}`);
            const skill = await response.json();
            
            // Update skill information
            const skillNameEl = document.getElementById('skill-name');
            // const skillLevelEl = document.getElementById('skill-level');
            const skillDescEl = document.getElementById('skill-description');
            
            if (skillNameEl) skillNameEl.textContent = String(skill.name).toUpperCase();
            // if (skillLevelEl) skillLevelEl.textContent = `Level: ${skill.level || 'Unknown'}`;
            if (skillDescEl) skillDescEl.textContent = skill.description || 'No description available.';
            
            // Update prerequisites
            const prereqList = document.getElementById('prerequisites-list');
            if (prereqList) {
                if (skill.prerequisites && skill.prerequisites.length > 0) {
                    prereqList.innerHTML = skill.prerequisites.map(prereq => 
                        `<li onclick="window.skillPanel.show('${prereq.id}')">${prereq.name}</li>`
                    ).join('');
                } else {
                    prereqList.innerHTML = '<li>No prerequisites</li>';
                }
            }
            
            // Update next skills
            const nextList = document.getElementById('next-skills-list');
            if (nextList) {
                if (skill.next_skills && skill.next_skills.length > 0) {
                    nextList.innerHTML = skill.next_skills.map(next => 
                        `<li onclick="window.skillPanel.show('${next.id}')">${next.name}</li>`
                    ).join('');
                } else {
                    nextList.innerHTML = '<li>No next skills</li>';
                }
            }
            
        } catch (error) {
            console.error('Error loading skill details:', error);
            const skillDescEl = document.getElementById('skill-description');
            if (skillDescEl) {
                skillDescEl.innerHTML = '<div class="error">Error loading skill details. Please try again.</div>';
            }
        }
    }

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message || !this.currentSkillId) return;
        
        const sendBtn = document.getElementById('chat-send-btn');
        const messagesContainer = document.getElementById('chat-messages');
        
        // Add user message to chat
        if (messagesContainer) {
            messagesContainer.innerHTML += `<div class="chat-message user">${message}</div>`;
        }
        
        if (input) input.value = '';
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.textContent = 'Sending...';
        }
        
        // Scroll to bottom
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        try {
            const response = await fetch(`/api/skill/${this.currentSkillId}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const chatResponse = await response.json();
            
            // Add AI response to chat
            if (messagesContainer) {
                messagesContainer.innerHTML += `<div class="chat-message ai">${chatResponse.ai_response}</div>`;
            }
            
            // Store in chat history
            this.chatHistory.push({
                user: message,
                ai: chatResponse.ai_response,
                timestamp: chatResponse.timestamp
            });
            
        } catch (error) {
            console.error('Error sending chat message:', error);
            if (messagesContainer) {
                messagesContainer.innerHTML += `<div class="chat-message ai">Sorry, I couldn't process your message. Please try again.</div>`;
            }
        }
        
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.textContent = 'Send';
        }
        
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // Reset chat UI to initial state (used when switching skills)
    resetChatUI() {
        console.log("resetChatUI");
        const messagesContainer = document.getElementById('chat-messages');
        const input = document.getElementById('chat-input');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="chat-message ai">
                    Hi! I can help you learn about this skill. What would you like to know?
                </div>
            `;
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        console.log(messagesContainer, "messagesContainer");
        console.log(input, "input");
        if (input) input.value = '';
        this.chatHistory = [];
    }
}

// Initialize the skill panel when the script loads
document.addEventListener('DOMContentLoaded', function() {
    window.skillPanel = new SkillPanel();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SkillPanel;
}

