document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('urlForm');
    const input = form.querySelector('input[type="text"]');
    const popup = document.getElementById('successPopup');

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const url = input.value;
        const studentId = document.getElementById('studentId').value;
        const studentName = document.getElementById('studentName').value;
        const studentProfession = document.getElementById('studentProfession').value;

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
            // Здесь вы можете показать сообщение об ошибке пользователю
        });
        input.value = '';
    });
});
