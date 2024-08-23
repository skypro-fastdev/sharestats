document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.action-buttons .btn');
    const sections = document.querySelectorAll('.content-section');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');

            // Деактивируем все кнопки и скрываем все секции
            buttons.forEach(btn => btn.classList.remove('active'));
            sections.forEach(section => section.classList.remove('active'));

            // Активируем нажатую кнопку и показываем соответствующую секцию
            this.classList.add('active');
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                targetSection.classList.add('active');
                console.log('Activated section:', targetId);
            } else {
                console.error('Target section not found:', targetId);
            }
        });
    });
});