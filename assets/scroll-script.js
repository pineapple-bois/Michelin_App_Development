// Function to scroll to the content top when the button is clicked
document.addEventListener('DOMContentLoaded', function () {
    // Wait for the DOM to be fully loaded
    var analysisButton = document.getElementById('analysis-button');
    if (analysisButton) {
        analysisButton.addEventListener('click', function () {
            // Scroll to the element with id='analysis-content-top'
            var targetElement = document.getElementById('analysis-content-top');
            if (targetElement) {
                targetElement.scrollIntoView({ behavior: 'smooth' });  // Smooth scroll
            }
        });
    }
});