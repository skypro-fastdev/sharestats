document.addEventListener('DOMContentLoaded', () => {
    const carousel = document.querySelector('.carousel');
    const items = Array.from(carousel.children);
    const nextButton = document.querySelector('.carousel-btn.next');
    const prevButton = document.querySelector('.carousel-btn.prev');
    const itemsToShow = 3; // Number of items to show at once
    const itemWidth = 320; // Width of each item
    const itemMargin = 20; // Margin between items
    const totalItems = items.length;

    let currentIndex = 0; // Start index

    function updateCarousel() {
        // Calculate the movement
        const movement = currentIndex * -(itemWidth + itemMargin);

        // Apply the transform with a smooth transition if smooth is true
        carousel.style.transform = `translateX(${movement}px)`;

        // Update visibility of items
        items.forEach((item, index) => {
            if (index >= currentIndex && index < currentIndex + itemsToShow) {
                item.style.opacity = '1';
                item.style.visibility = 'visible';
            } else {
                item.style.opacity = '0';
                item.style.visibility = 'hidden';
            }
        });

        updateButtons();
    }

    function updateButtons() {
        prevButton.disabled = currentIndex === 0;
        nextButton.disabled = currentIndex >= totalItems - itemsToShow;
    }

    nextButton.addEventListener('click', () => {
        if (currentIndex < totalItems - itemsToShow) {
            currentIndex += itemsToShow; // Move by three items
            updateCarousel();
        }
    });

    prevButton.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex -= itemsToShow; // Move by three items
            updateCarousel();
        }
    });

    // Set initial width of the carousel
    carousel.style.width = `${(itemWidth + itemMargin) * totalItems}px`;

    updateCarousel(false); // Initial setup without animation
});