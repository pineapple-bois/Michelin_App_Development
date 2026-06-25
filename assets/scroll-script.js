document.addEventListener('click', function (event) {
    var navButton = event.target.closest && event.target.closest('#analysis-button, #economics-button, #wine-button');
    if (!navButton) {
        return;
    }

    var scrollTargets = {
        'analysis-button': 'analysis-content-top',
        'economics-button': 'demographics-content-top',
        'wine-button': 'wine-content-top'
    };

    function scrollToSectionTop() {
        var targetElement = document.getElementById(scrollTargets[navButton.id]);
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: 'smooth' });
        }
    }

    scrollToSectionTop();
    window.setTimeout(scrollToSectionTop, 250);
});
