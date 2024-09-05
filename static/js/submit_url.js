document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('urlForm');
    const input = form.querySelector('input[type="text"]');
    const popup = document.getElementById('successPopup');

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const url = input.value.trim();
        const studentId = document.getElementById('studentId').value;
        const studentName = document.getElementById('studentName').value;
        const studentProfession = document.getElementById('studentProfession').value;

        // Проверка: URL не должен быть пустым
        if (url === '') {
            alert('Пожалуйста, введите ссылку!');
            return;
        }

        fetch('/share/submit-url', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentId,
                student_name: studentName,
                student_profession: studentProfession,
                url: url,
            }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'processing') {
                    // Отправляем событие в Яндекс Метрику при успешной обработке
                    if (typeof ym !== 'undefined') {
                        ym(97943495, 'reachGoal', 'stats_send_link');
                    }

                    popup.style.display = 'block';
                    setTimeout(() => {
                        popup.style.display = 'none';
                    }, 4000);
                } else {
                    console.warn('Unexpected response from server:', data);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
            });
        input.value = '';
    });
});
