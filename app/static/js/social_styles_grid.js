/**
 * Social Styles Grid Interactive Features
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all social styles grids on the page
    initializeSocialStylesGrids();
});

function initializeSocialStylesGrids() {
    const svgGrids = document.querySelectorAll('.social-styles-svg');
    
    svgGrids.forEach(svg => {
        // Add SVG animation for pulse effect
        const svgNS = "http://www.w3.org/2000/svg";
        const style = document.createElementNS(svgNS, "style");
        style.textContent = `
            @keyframes pulse-svg {
                0% { r: 6; opacity: 0.5; }
                70% { r: 12; opacity: 0; }
                100% { r: 6; opacity: 0; }
            }
            .pulse-animation {
                animation: pulse-svg 2s infinite;
            }
            
            .quadrant-bg {
                transition: all 0.2s ease;
            }
            
            .quadrant-bg:hover {
                fill-opacity: 0.05;
                cursor: pointer;
                stroke-width: 1;
                stroke-opacity: 0.7;
            }
            
            .quadrant-label-group {
                transition: transform 0.2s ease;
            }
            
            .quadrant-label-group:hover {
                transform: scale(1.02);
            }
        `;
        svg.appendChild(style);
        
        // Add interactivity to quadrants
        const quadrants = svg.querySelectorAll('.quadrant-bg');
        quadrants.forEach(quadrant => {
            // Set stroke color based on quadrant
            const quadrantName = quadrant.getAttribute('data-quadrant');
            let strokeColor;
            
            switch(quadrantName) {
                case 'ANALYTICAL':
                    strokeColor = '#1565c0';
                    break;
                case 'DRIVER':
                    strokeColor = '#c62828';
                    break;
                case 'AMIABLE':
                    strokeColor = '#2e7d32';
                    break;
                case 'EXPRESSIVE':
                    strokeColor = '#f57c00';
                    break;
                default:
                    strokeColor = '#757575';
            }
            
            // If stroke is not already set (for custom grids)
            if (!quadrant.getAttribute('stroke')) {
                quadrant.setAttribute('stroke', strokeColor);
                quadrant.setAttribute('stroke-width', '0.5');
                quadrant.setAttribute('stroke-opacity', '0.2');
            }
            
            // Add hover effects
            quadrant.addEventListener('mouseover', function() {
                // Get current stroke color
                const currentStroke = this.getAttribute('stroke');
                
                // Highlight the quadrant
                this.setAttribute('stroke-width', '1');
                this.setAttribute('stroke-opacity', '0.7');
                
                // Add subtle fill color on hover for white backgrounds
                if (this.getAttribute('fill') === '#ffffff') {
                    this.setAttribute('fill-opacity', '0.05');
                    this.setAttribute('fill', currentStroke);
                }
                
                // Scale up the label
                const quadrantName = this.getAttribute('data-quadrant');
                svg.querySelectorAll(`.quadrant-label-group[data-quadrant="${quadrantName}"]`).forEach(label => {
                    label.setAttribute('transform', 'scale(1.02)');
                });
            });
            
            quadrant.addEventListener('mouseout', function() {
                // Reset the quadrant
                this.setAttribute('stroke-width', '0.5');
                this.setAttribute('stroke-opacity', '0.5');
                
                // Reset fill for white backgrounds
                if (this.getAttribute('fill-opacity') === '0.05') {
                    this.setAttribute('fill', '#ffffff');
                    this.setAttribute('fill-opacity', '1');
                }
                
                // Reset the label
                const quadrantName = this.getAttribute('data-quadrant');
                svg.querySelectorAll(`.quadrant-label-group[data-quadrant="${quadrantName}"]`).forEach(label => {
                    label.setAttribute('transform', 'scale(1)');
                });
            });
        });
    });
} 