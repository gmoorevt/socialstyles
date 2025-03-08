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
                0% { r: 8; opacity: 0.6; }
                70% { r: 20; opacity: 0; }
                100% { r: 8; opacity: 0; }
            }
            .pulse-animation {
                animation: pulse-svg 2s infinite;
            }
            
            .quadrant-bg {
                transition: all 0.3s ease;
            }
            
            .quadrant-bg:hover {
                fill-opacity: 0.3;
                cursor: pointer;
                stroke-width: 2;
                stroke-opacity: 0.8;
            }
            
            .quadrant-label-group {
                transition: transform 0.3s ease;
            }
            
            .quadrant-label-group:hover {
                transform: scale(1.05);
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
                    strokeColor = '#0d6efd';
                    break;
                case 'DRIVER':
                    strokeColor = '#dc3545';
                    break;
                case 'AMIABLE':
                    strokeColor = '#198754';
                    break;
                case 'EXPRESSIVE':
                    strokeColor = '#ffc107';
                    break;
                default:
                    strokeColor = '#6c757d';
            }
            
            quadrant.setAttribute('stroke', strokeColor);
            quadrant.setAttribute('stroke-width', '1');
            quadrant.setAttribute('stroke-opacity', '0.3');
            
            // Add hover effects
            quadrant.addEventListener('mouseover', function() {
                // Highlight the quadrant
                this.setAttribute('stroke-width', '2');
                this.setAttribute('stroke-opacity', '0.8');
                
                // Scale up the label
                const quadrantName = this.getAttribute('data-quadrant');
                svg.querySelectorAll(`.quadrant-label-group[data-quadrant="${quadrantName}"]`).forEach(label => {
                    label.setAttribute('transform', 'scale(1.05)');
                });
            });
            
            quadrant.addEventListener('mouseout', function() {
                // Reset the quadrant
                this.setAttribute('stroke-width', '1');
                this.setAttribute('stroke-opacity', '0.3');
                
                // Reset the label
                const quadrantName = this.getAttribute('data-quadrant');
                svg.querySelectorAll(`.quadrant-label-group[data-quadrant="${quadrantName}"]`).forEach(label => {
                    label.setAttribute('transform', 'scale(1)');
                });
            });
        });
    });
} 