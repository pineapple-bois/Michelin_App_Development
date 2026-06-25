document.addEventListener('click', function (event) {
    var analysisButton = event.target.closest && event.target.closest('#analysis-button');
    if (!analysisButton) {
        return;
    }

    var targetElement = document.getElementById('analysis-content-top');
    if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth' });
    }
});
