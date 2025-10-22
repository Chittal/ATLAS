/**
 * Learning Nodes Graph Implementation
 * 
 * This file contains the saved implementation for displaying learning nodes
 * as a connected graph using Cytoscape.js. This was replaced with a horizontal
 * list view but is preserved here for future use.
 */

// Function to initialize the learning nodes graph (SAVED FOR FUTURE USE)
async function initializeLearningNodesGraph(learningNodes, edges) {
    try {
        // Create nodes for learning nodes
        const nodes = learningNodes.map((node, index) => ({
            data: {
                id: node.id,
                name: node.name,
                description: node.description || '',
                depth: node.depth,
                step: index + 1
            },
            classes: `learning-node depth-${node.depth}`
        }));
        
        // Create edges from the API data
        const graphEdges = edges.map(edge => ({
            data: {
                id: `${edge.source}-${edge.target}`,
                source: edge.source,
                target: edge.target
            },
            classes: 'learning-edge'
        }));
        
        // Get base styles
        const styleText = await (await fetch(window.urlPrefix + '/static/skills-graph.cycss')).text();
        
        // Add custom styles for learning nodes
        const customStyles = `
            .learning-node {
                background-color: #17a2b8;
                border-color: #138496;
                border-width: 2px;
                label: data(name);
                font-size: 12px;
                text-valign: center;
                text-halign: center;
                width: 120px;
                height: 60px;
                shape: roundrectangle;
            }
            .learning-node.depth-0 {
                background-color: #28a745;
                border-color: #1e7e34;
            }
            .learning-node.depth-1 {
                background-color: #ffc107;
                border-color: #e0a800;
                color: #212529;
            }
            .learning-node.depth-2 {
                background-color: #dc3545;
                border-color: #c82333;
            }
            .learning-edge {
                line-color: #6c757d;
                line-width: 2px;
                target-arrow-color: #6c757d;
                target-arrow-shape: triangle;
            }
        `;
        
        // Initialize Cytoscape for learning nodes
        const learningCy = cytoscape({
            container: document.getElementById('learning-nodes-cy'),
            elements: { nodes, edges: graphEdges },
            style: styleText + customStyles,
            layout: { name: 'cose' },
        });
        
        // Add event handlers
        learningCy.on('tap', 'node', function(evt) {
            const node = evt.target;
            const nodeId = node.data('id');
            const nodeName = node.data('name');
            
            console.log(`🎯 Clicked learning node: ${nodeName}`);
            
            if (window.chatWidget) {
                const message = `I want to learn more about "${nodeName}". Can you provide detailed guidance on this learning node?`;
                
                if (!window.chatWidget.isOpen) {
                    window.chatWidget.openChat();
                    setTimeout(() => {
                        window.chatWidget.setInputValue(message);
                    }, 300);
                } else {
                    window.chatWidget.setInputValue(message);
                }
            }
        });
        
        // Add hover effects
        learningCy.on('mouseover', 'node', function(evt) {
            const node = evt.target;
            node.style('background-color', '#e3f2fd');
            node.style('border-color', '#2196f3');
        });

        learningCy.on('mouseout', 'node', function(evt) {
            const node = evt.target;
            // Reset to original color based on depth
            const depth = node.data('depth');
            const colors = {
                0: '#28a745',
                1: '#ffc107', 
                2: '#dc3545'
            };
            const borderColors = {
                0: '#1e7e34',
                1: '#e0a800',
                2: '#c82333'
            };
            node.style('background-color', colors[depth] || '#17a2b8');
            node.style('border-color', borderColors[depth] || '#138496');
        });
        
        // Hide loading indicator
        document.getElementById('learning-nodes-loading').classList.add('loaded');
        
        // Fit to content
        setTimeout(() => {
            learningCy.fit(null, 50);
        }, 100);
        
    } catch (error) {
        console.error('Error initializing learning nodes graph:', error);
        document.getElementById('learning-nodes-loading').innerHTML = `
            <div style="color: #dc3545;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor" style="margin-bottom: 10px;">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
                <div>Error loading learning nodes graph</div>
            </div>
        `;
    }
}

/**
 * Usage Instructions:
 * 
 * To use this graph implementation in the future:
 * 1. Include this file in your HTML: <script src="/static/learning-nodes-graph.js"></script>
 * 2. Make sure you have a container with id 'learning-nodes-cy'
 * 3. Call: initializeLearningNodesGraph(learningNodes, edges)
 * 
 * Required HTML structure:
 * <div id="learning-nodes-cy"></div>
 * <div id="learning-nodes-loading">Loading...</div>
 * 
 * Required CSS classes:
 * .learning-node, .learning-node.depth-0, .learning-node.depth-1, .learning-node.depth-2
 * .learning-edge
 * #learning-nodes-loading.loaded
 */
