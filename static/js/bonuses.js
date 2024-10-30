document.addEventListener('DOMContentLoaded', function() {
    const buttons = document.querySelectorAll('.action-buttons .btn');
    const sections = document.querySelectorAll('.content-section');
    const summaries = document.querySelectorAll('.product-summary');

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

                // Отправляем событие в Яндекс Метрику, если активирована секция products-section
                if (targetId === 'products-section') {
                    if (typeof ym !== 'undefined') {
                        ym(97943495, 'reachGoal', 'bonus_products_tab');
                        console.log('Sent Yandex Metrika event: bonus_products_tab');
                    } else {
                        console.error('Yandex Metrika is not defined');
                    }
                }
            } else {
                console.error('Target section not found:', targetId);
            }
        });
    });

    // Добавляем обработчик событий для summary элементов
    summaries.forEach(summary => {
        summary.addEventListener('click', function() {
            if (typeof ym !== 'undefined') {
                ym(97943495, 'reachGoal', 'bonus_purchase');
                console.log('Sent Yandex Metrika event: bonus_purchase');
            } else {
                console.error('Yandex Metrika is not defined');
            }
        });
    });
});