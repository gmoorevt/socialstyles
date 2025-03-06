// Main JavaScript file for Social Styles Assessment

document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Enable Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Flash message auto-dismiss
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Assessment form validation
    var assessmentForm = document.querySelector('form[action*="take_assessment"]');
    if (assessmentForm) {
        assessmentForm.addEventListener('submit', function(event) {
            var radioGroups = document.querySelectorAll('input[type="radio"][required]');
            var groupNames = {};
            
            // Get all required radio button groups
            radioGroups.forEach(function(radio) {
                groupNames[radio.name] = true;
            });
            
            // Check if all groups have a selection
            var isValid = true;
            Object.keys(groupNames).forEach(function(groupName) {
                var checked = document.querySelector('input[name="' + groupName + '"]:checked');
                if (!checked) {
                    isValid = false;
                    
                    // Find the question container and add error class
                    var container = document.querySelector('input[name="' + groupName + '"]').closest('.mb-4');
                    container.classList.add('border', 'border-danger');
                    
                    // Add error message if it doesn't exist
                    if (!container.querySelector('.text-danger')) {
                        var errorMsg = document.createElement('div');
                        errorMsg.className = 'text-danger mt-2 small';
                        errorMsg.textContent = 'Please select an option for this question.';
                        container.appendChild(errorMsg);
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
                
                // Scroll to first error
                var firstError = document.querySelector('.border-danger');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                
                // Show overall error message
                var formAlert = document.createElement('div');
                formAlert.className = 'alert alert-danger alert-dismissible fade show mt-3';
                formAlert.innerHTML = 'Please answer all questions before submitting. <button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
                
                var formTop = assessmentForm.querySelector('.card-body');
                formTop.insertBefore(formAlert, formTop.firstChild);
            }
        });
        
        // Remove error styling when an option is selected
        assessmentForm.addEventListener('change', function(event) {
            if (event.target.type === 'radio') {
                var container = event.target.closest('.mb-4');
                container.classList.remove('border', 'border-danger');
                
                var errorMsg = container.querySelector('.text-danger');
                if (errorMsg) {
                    errorMsg.remove();
                }
            }
        });
    }

    // Add animation to assessment cards
    const questionCards = document.querySelectorAll('.question-card');
    questionCards.forEach((card, index) => {
        card.style.setProperty('--animation-order', index);
    });

    // Enhanced radio button selection for assessment
    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach(input => {
        // Add click event to each radio input
        input.addEventListener('change', function() {
            // Get all radio inputs in the same question group
            const questionGroup = this.closest('.question-card');
            const allInputs = questionGroup.querySelectorAll('.form-check');
            
            // Remove active class from all options
            allInputs.forEach(check => {
                check.classList.remove('active');
            });
            
            // Add active class to selected option
            this.closest('.form-check').classList.add('active');
            
            // Visual feedback animation
            this.closest('.question-card').classList.add('answered');
            
            // Check if all questions are answered
            checkAllQuestionsAnswered();
        });
    });
    
    // Function to check if all questions are answered
    function checkAllQuestionsAnswered() {
        const totalQuestions = document.querySelectorAll('.question-card').length;
        const answeredQuestions = document.querySelectorAll('.question-card.answered').length;
        
        const progressPercent = Math.round((answeredQuestions / totalQuestions) * 100);
        
        // Update progress if element exists
        const progressBar = document.getElementById('assessment-progress');
        if (progressBar) {
            progressBar.style.width = progressPercent + '%';
            progressBar.setAttribute('aria-valuenow', progressPercent);
            document.getElementById('progress-text').textContent = `${answeredQuestions}/${totalQuestions} questions answered (${progressPercent}%)`;
        }
        
        // Enable submit button when all questions are answered
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn && answeredQuestions === totalQuestions) {
            submitBtn.classList.add('pulse-animation');
        }
    }
    
    // Add smooth scrolling to next question section
    const sectionLinks = document.querySelectorAll('.section-link');
    sectionLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            window.scrollTo({
                top: targetElement.offsetTop - 100,
                behavior: 'smooth'
            });
        });
    });
    
    // Add hover effect to scale points in instructions
    const scalePoints = document.querySelectorAll('.scale-point');
    scalePoints.forEach((point, index) => {
        point.addEventListener('mouseenter', function() {
            scalePoints.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // Add progress bar to assessment if it doesn't exist
    const assessmentForm = document.querySelector('form[action*="assessment"]');
    if (assessmentForm && !document.getElementById('assessment-progress-container')) {
        const progressContainer = document.createElement('div');
        progressContainer.id = 'assessment-progress-container';
        progressContainer.className = 'sticky-top bg-white py-2 px-3 mb-4 shadow-sm rounded';
        progressContainer.style.top = '70px';
        progressContainer.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="text-muted fs-6" id="progress-text">0/${document.querySelectorAll('.question-card').length} questions answered (0%)</span>
                <button type="button" class="btn btn-sm btn-outline-primary" id="scroll-to-next">Next unanswered</button>
            </div>
            <div class="progress" style="height: 8px;">
                <div id="assessment-progress" class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
        
        const formStart = assessmentForm.querySelector('.card');
        assessmentForm.insertBefore(progressContainer, formStart);
        
        // Add functionality to "Next unanswered" button
        document.getElementById('scroll-to-next').addEventListener('click', function() {
            const unanswered = document.querySelector('.question-card:not(.answered)');
            if (unanswered) {
                window.scrollTo({
                    top: unanswered.offsetTop - 150,
                    behavior: 'smooth'
                });
                unanswered.classList.add('highlight-pulse');
                setTimeout(() => {
                    unanswered.classList.remove('highlight-pulse');
                }, 2000);
            }
        });
    }
    
    // Add pulse animation class
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(67, 97, 238, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(67, 97, 238, 0); }
            100% { box-shadow: 0 0 0 0 rgba(67, 97, 238, 0); }
        }
        .pulse-animation {
            animation: pulse 1.5s infinite;
        }
        @keyframes highlight {
            0% { background-color: rgba(67, 97, 238, 0.1); }
            50% { background-color: rgba(67, 97, 238, 0.2); }
            100% { background-color: rgba(67, 97, 238, 0.1); }
        }
        .highlight-pulse {
            animation: highlight 1s ease-in-out;
        }
    `;
    document.head.appendChild(style);
}); 