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
        this.currentPath = null; // Track current highlighted path
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadMessageHistory();
        this.setupAutoResize();
        
        // Set initial z-index class
        const chatWidget = document.querySelector('.chat-widget');
        if (chatWidget) {
            chatWidget.classList.add('closed');
        }
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
        
        // Handle start learning button
        this.setupStartLearningButton();
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
        const chatWidget = document.querySelector('.chat-widget');
        
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

        // Update z-index classes
        if (chatWidget) {
            chatWidget.classList.remove('closed');
            chatWidget.classList.add('open');
        }
    }

    closeChat() {
        const chatWindow = document.getElementById('chat-window');
        const toggleBtn = document.getElementById('chat-toggle');
        const chatWidget = document.querySelector('.chat-widget');
        
        if (chatWindow) {
            chatWindow.classList.add('hidden');
            this.isOpen = false;
        }

        if (toggleBtn) {
            toggleBtn.style.transform = 'rotate(0deg)';
        }

        // Update z-index classes
        if (chatWidget) {
            chatWidget.classList.remove('open');
            chatWidget.classList.add('closed');
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
        console.log('Processing message:', message);
        console.log('Routing to handleGeneralQuery');
        return await this.handleGeneralQuery(message);
    }

    async handleGeneralQuery(message) {
        // For general queries, we can use the existing chat API
        try {
            console.log('Calling /api/general/chat with message:', message);
            // Use a default skill ID for general queries
            const response = await fetch(window.urlPrefix + '/api/general/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('Received response from API:', data);
                
                // Check if this is a route planning response with path data
                console.log('Checking for route planning data:', {
                    hasPathData: !!data.path_data,
                    category: data.agent_metadata?.category,
                    pathData: data.path_data,
                    pathDataType: typeof data.path_data,
                    pathDataKeys: data.path_data ? Object.keys(data.path_data) : 'N/A',
                    agentMetadata: data.agent_metadata,
                    agentMetadataType: typeof data.agent_metadata
                });
                
                const hasPathData = data.path_data && data.path_data.path && data.path_data.path.length > 0;
                const isRoutePlanning = data.agent_metadata && data.agent_metadata.category === 'ROUTE_PLANNING';
                
                console.log('Condition checks:', {
                    hasPathData,
                    isRoutePlanning,
                    willHighlight: hasPathData && isRoutePlanning
                });
                
                if (hasPathData && isRoutePlanning) {
                    console.log('Route planning detected, highlighting path:', data.path_data);
                    
                    // Try to trigger the existing Path button functionality
                    // Check if we're on the roadmap page and the Path button exists
                    const startSkill = data.path_data.start_skill;
                    const targetSkill = data.path_data.target_skill;
                    const pathButton = document.getElementById('path-da-agents');

                    if (pathButton) {
                        console.log('Found Path button, clicking it to highlight path');
                        console.log('Using global highlightPathBetweenSkills function');
                        // Extract skill names from path data if available
                        const pathStartSkill = data.path_data.path[0]?.name || startSkill || 'data analyst';
                        const pathTargetSkill = data.path_data.path[data.path_data.path.length - 1]?.name || targetSkill || 'ai agents';
                        window.highlightPathBetweenSkills(pathStartSkill, pathTargetSkill);
                    } else {
                        console.log('No path highlighting method found, trying direct highlighting');
                        // Fallback to direct highlighting
                        setTimeout(() => {
                            this.highlightPath(data.path_data.path);
                        }, 500);
                    }
                    
                    // Show the Start Learning button after highlighting the path
                    setTimeout(() => {
                        this.showStartLearningButton(data.path_data);
                    }, 1000); // Wait a bit for highlighting to complete
                } else {
                    console.log('No path highlighting:', {
                        reason: !hasPathData ? 'missing or empty path_data' : 'not route planning category',
                        hasPathData,
                        isRoutePlanning,
                        category: data.agent_metadata?.category
                    });
                    
                    // Hide the Start Learning button if no path is available
                    this.hideStartLearningButton();
                }
                
                return data.ai_response || this.getDefaultResponse(message);
            } else {
                console.log('API response not ok:', response.status);
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
        // Handle both object and string formats
        const skillNames = path.map(item => {
            if (typeof item === 'object' && item.name) {
                return item.name;
            } else {
                return this.getSkillNameById(item);
            }
        }).filter(Boolean);
        
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

    highlightPath(pathData) {
        console.log('🎯 highlightPath called with:', pathData);
        console.log('🔍 Cytoscape available:', typeof cy !== 'undefined');
        
        // Helper function to actually perform highlighting
        const performHighlighting = () => {
            // Debug: Let's see what's actually available
            console.log('🔍 Debugging Cytoscape access:');
            console.log('- window object keys:', Object.keys(window).filter(key => key.toLowerCase().includes('cy')));
            console.log('- cy in window:', 'cy' in window);
            console.log('- window.cy:', window.cy);
            console.log('- typeof window.cy:', typeof window.cy);
            console.log('- window.cy methods:', window.cy ? Object.getOwnPropertyNames(Object.getPrototypeOf(window.cy)) : 'N/A');
            
            // Try to get Cytoscape instance from window
            const cyInstance = window.cy || cy;
            
            // Use the same approach as the Path button - direct access to global cy
            // The Path button works because it's in the same scope as Cytoscape initialization
            // We replicate that approach here by accessing the global 'cy' variable directly
            if (typeof cyInstance !== 'undefined' && cyInstance && typeof cyInstance.elements === 'function') {
                try {
                    const elements = cyInstance.elements();
                    console.log('📊 Graph elements:', elements.length);
                    
                    // Check if graph has elements
                    if (elements.length === 0) {
                        console.log('❌ Graph has no elements yet - skipping highlighting');
                        return;
                    }
            
                    // Reset previous highlights
                    elements.removeClass('highlighted not-path');
                    cyInstance.nodes().unselect();

            // Dim everything by default
            cyInstance.elements().addClass('not-path');

            // Handle both object and string formats
            const pathIds = pathData.map(item => typeof item === 'object' ? item.id : item);
            console.log('🆔 Path IDs to highlight:', pathIds);

            // Highlight path nodes
            let highlightedNodes = 0;
            pathIds.forEach(id => {
                const node = cyInstance.getElementById(id);
                if (node) {
                    node.addClass('highlighted');
                    node.removeClass('not-path');
                    node.select();
                    highlightedNodes++;
                    console.log(`✅ Highlighted node: ${id}`);
                } else {
                    console.log(`❌ Node not found: ${id}`);
                }
            });

            // Highlight path edges
            let highlightedEdges = 0;
            for (let i = 0; i < pathIds.length - 1; i++) {
                const edgeId = `${pathIds[i]}-${pathIds[i + 1]}`;
                const edge = cyInstance.getElementById(edgeId);
                if (edge) {
                    edge.addClass('highlighted');
                    edge.removeClass('not-path');
                    highlightedEdges++;
                    console.log(`✅ Highlighted edge: ${edgeId}`);
                } else {
                    console.log(`❌ Edge not found: ${edgeId}`);
                }
            }

            console.log(`📈 Highlighted ${highlightedNodes} nodes and ${highlightedEdges} edges`);

            // Fit to highlighted elements
            const highlighted = cyInstance.elements('.highlighted');
            if (highlighted && highlighted.length > 0) {
                cyInstance.fit(highlighted, 80);
                console.log('🎯 Fitted view to highlighted elements');
            } else {
                console.log('❌ No elements highlighted, cannot fit view');
            }
                } catch (error) {
                    console.error('❌ Error during path highlighting:', error);
                }
            } else {
                console.log('❌ Cytoscape not available - cannot highlight path');
            }
        };
        
        // Check if we're on a page with Cytoscape
        const cyContainer = document.getElementById('cy');
        if (!cyContainer) {
            console.log('❌ No Cytoscape container found - not on graph page');
            return;
        }
        
        // Check if we're in the middle of a page load or Cytoscape initialization
        if (document.readyState !== 'complete') {
            console.log('⏳ Page still loading, waiting...');
            return;
        }
        
        // Try to highlight with multiple retries
        let retryCount = 0;
        const maxRetries = 3;
        
        const attemptHighlighting = () => {
            retryCount++;
            console.log(`🔄 Highlighting attempt ${retryCount}/${maxRetries}`);
            
            performHighlighting();
            
            // If still not working and we haven't exceeded max retries, try again
            const cyInstance = window.cy || cy;
            const needsRetry = retryCount < maxRetries && 
                (typeof cyInstance === 'undefined' || 
                 !cyInstance || 
                 typeof cyInstance.elements !== 'function' || 
                 cyInstance.elements().length === 0);
                 
            console.log('🔍 Retry check:', {
                retryCount,
                maxRetries,
                needsRetry,
                cyInstanceType: typeof cyInstance,
                cyInstanceExists: !!cyInstance,
                cyInstanceElements: typeof cyInstance?.elements,
                elementsLength: cyInstance?.elements ? cyInstance.elements().length : 'N/A'
            });
                 
            if (needsRetry) {
                const delay = retryCount * 1000; // Increasing delay: 1s, 2s, 3s
                console.log(`⏳ Cytoscape not ready, retrying in ${delay}ms...`);
                setTimeout(attemptHighlighting, delay);
            } else if (retryCount >= maxRetries) {
                console.log('❌ Max retries reached - giving up on highlighting');
            }
        };
        
        // Start the first attempt
        attemptHighlighting();
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
        // Skill panel integration removed
        this.currentSkill = null;
    }

    setupStartLearningButton() {
        const startLearningBtn = document.getElementById('start-learning-btn');
        if (startLearningBtn) {
            startLearningBtn.addEventListener('click', () => {
                this.handleStartLearning();
            });
        }
    }

    showStartLearningButton(pathData) {
        console.log('🎯 Showing Start Learning button for path:', pathData);
        const startLearningSection = document.getElementById('start-learning-section');
        if (startLearningSection) {
            this.currentPath = pathData;
            startLearningSection.classList.remove('hidden');
            
            // Update button text with path info if available
            const startSkill = pathData.path && pathData.path[0] ? pathData.path[0].name : 'First Skill';
            const endSkill = pathData.path && pathData.path[pathData.path.length - 1] ? pathData.path[pathData.path.length - 1].name : 'Target Skill';
            
            const buttonText = startLearningSection.querySelector('span');
            if (buttonText) {
                buttonText.textContent = `Start Learning: ${startSkill} → ${endSkill}`;
            }
        }
    }

    hideStartLearningButton() {
        console.log('🎯 Hiding Start Learning button');
        const startLearningSection = document.getElementById('start-learning-section');
        if (startLearningSection) {
            this.currentPath = null;
            startLearningSection.classList.add('hidden');
            
            // Reset button text
            const buttonText = startLearningSection.querySelector('span');
            if (buttonText) {
                buttonText.textContent = 'Start Learning';
            }
        }
    }

    async handleStartLearning() {
        console.log('🎯 Start Learning button clicked!');
        
        if (!this.currentPath) {
            console.log('❌ No current path available');
            return;
        }

        // Extract start and end skills from the path
        const startSkill = this.currentPath.path[0]?.name || this.currentPath.path[0]?.id || 'data analyst';
        const endSkill = this.currentPath.path[this.currentPath.path.length - 1]?.name || 
                        this.currentPath.path[this.currentPath.path.length - 1]?.id || 'ai agents';

        // Add a brief message to the chat
        const pathNames = this.currentPath.path.map(skill => skill.name || skill.id);
        const pathDescription = pathNames.join(' → ');
        
        const savingMessage = `🚀 **Saving Your Learning Path!**\n\nYour path: ${pathDescription}\n\nSaving to your progress tracker...`;
        this.addMessage(savingMessage, 'ai');
        
        try {
            // Save the learning track to PocketBase
            const trackData = {
                start_skill: startSkill,
                target_skill: endSkill,
                skill_path: this.currentPath.path
            };
            
            console.log('💾 Saving learning track:', trackData);
            
            const saveResponse = await fetch(window.urlPrefix + '/api/route-planning/start-learning', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(trackData)
            });
            
            if (saveResponse.ok) {
                const saveResult = await saveResponse.json();
                console.log('✅ Learning track saved successfully:', saveResult);
                
                // Update message with success
                const successMessage = `✅ **Learning Path Saved!**\n\nYour progress will be tracked. Taking you to the learning environment...`;
                this.addMessage(successMessage, 'ai');
                
                // Navigate to learning path page with the roadmap path ID
                setTimeout(() => {
                    const userRoadmapPathId = saveResult.data?.user_roadmap_path_id;
                    if (userRoadmapPathId) {
                        window.location.href = window.urlPrefix + `/learning-path?start=${encodeURIComponent(startSkill)}&end=${encodeURIComponent(endSkill)}&roadmap_path_id=${userRoadmapPathId}`;
                    } else {
                        window.location.href = window.urlPrefix + `/learning-path?start=${encodeURIComponent(startSkill)}&end=${encodeURIComponent(endSkill)}`;
                    }
                }, 1500); // 1.5 second delay to show the success message
                
            } else {
                console.error('❌ Failed to save learning track:', saveResponse.status);
                const errorMessage = `❌ **Error Saving Path**\n\nCould not save your learning path. Taking you to the learning environment anyway...`;
                this.addMessage(errorMessage, 'ai');
                
                // Still navigate even if save fails
                setTimeout(() => {
                    window.location.href = `/learning-path?start=${encodeURIComponent(startSkill)}&end=${encodeURIComponent(endSkill)}`;
                }, 1500);
            }
            
        } catch (error) {
            console.error('❌ Error saving learning track:', error);
            const errorMessage = `❌ **Error Saving Path**\n\nCould not save your learning path. Taking you to the learning environment anyway...`;
            this.addMessage(errorMessage, 'ai');
            
            // Still navigate even if save fails
            setTimeout(() => {
                window.location.href = `/learning-path?start=${encodeURIComponent(startSkill)}&end=${encodeURIComponent(endSkill)}`;
            }, 1500);
        }
        
        console.log('✅ Learning journey started for path:', this.currentPath);
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
        this.currentPath = null;
        this.hideStartLearningButton();
        
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
