/**
 * Social Styles Grid — shared geometry + interactive features.
 *
 * The position/quadrant math here is the JavaScript mirror of
 * app/assessment/geometry.py and MUST stay numerically identical.
 * tests/test_geometry.py asserts parity between the two by running this
 * module under Node. Keep the formulas in sync.
 */
(function (global) {
    'use strict';

    var LO = 1, HI = 4, MIDPOINT = 2.5;
    var SVG_ORIGIN = 50, SVG_SPAN = 300;
    var QUADRANT_COLORS = {
        ANALYTICAL: '#1565c0',
        DRIVER: '#c62828',
        AMIABLE: '#2e7d32',
        EXPRESSIVE: '#f57c00'
    };

    function clampNormalize(value, lo, hi) {
        return (Math.min(Math.max(value, lo), hi) - lo) / (hi - lo);
    }

    // Returns [nx, ny] in 0..1. See geometry.py normalize_position.
    function normalizePosition(assertiveness, responsiveness) {
        return [clampNormalize(assertiveness, LO, HI), clampNormalize(responsiveness, LO, HI)];
    }

    // Returns [x, y] in the 400x400 SVG grid (plot area 50-350).
    function svgPosition(assertiveness, responsiveness) {
        var n = normalizePosition(assertiveness, responsiveness);
        return [SVG_ORIGIN + n[0] * SVG_SPAN, SVG_ORIGIN + n[1] * SVG_SPAN];
    }

    // Returns [xPct, yPct] for the percentage-positioned grid.
    function percentPosition(assertiveness, responsiveness) {
        var n = normalizePosition(assertiveness, responsiveness);
        return [n[0] * 100, n[1] * 100];
    }

    // Strict '>' against the midpoint — 2.5 is the LOW side.
    function quadrant(assertiveness, responsiveness) {
        var highA = assertiveness > MIDPOINT;
        var highR = responsiveness > MIDPOINT;
        if (highA && highR) return 'EXPRESSIVE';
        if (highA && !highR) return 'DRIVER';
        if (!highA && highR) return 'AMIABLE';
        return 'ANALYTICAL';
    }

    function quadrantColor(assertiveness, responsiveness) {
        return QUADRANT_COLORS[quadrant(assertiveness, responsiveness)];
    }

    var SocialStylesGrid = {
        LO: LO, HI: HI, MIDPOINT: MIDPOINT,
        QUADRANT_COLORS: QUADRANT_COLORS,
        normalizePosition: normalizePosition,
        svgPosition: svgPosition,
        percentPosition: percentPosition,
        quadrant: quadrant,
        quadrantColor: quadrantColor
    };

    global.SocialStylesGrid = SocialStylesGrid;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = SocialStylesGrid;
    }

    // ---- DOM interactivity (browser only) ----
    if (typeof document === 'undefined') {
        return;
    }

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
})(typeof globalThis !== 'undefined' ? globalThis : this);
