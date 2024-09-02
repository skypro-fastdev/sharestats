document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('quizForm');
    const popup = document.getElementById('successPopup');
    const popupTitle = document.getElementById('popupTitle');
    const popupMessage = document.getElementById('popupMessage');
    const popupImage = document.getElementById('popupImage');

    function showPopup(isSuccess, message) {
        popupTitle.textContent = isSuccess ? 'Готово!' : 'Ошибка!';
        popupMessage.textContent = message;
        popupImage.src = isSuccess ?
            popup.dataset.successImage :
            popup.dataset.errorImage;
        popup.style.display = 'block';
        setTimeout(() => {
            popup.style.display = 'none';
        }, 3000);
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const studentId = document.getElementById('studentId').value;
        if (!studentId) {
            showPopup(false, 'Ошибка: Идентификатор студента отсутствует');
            return;
        }

        let answers = {
            student_id: studentId,
        };
        const questions = document.querySelectorAll('.question');

        questions.forEach(question => {
            const questionId = question.querySelector('input[type="radio"]').name;
            const selectedOption = question.querySelector('input[type="radio"]:checked');

            if (selectedOption) {
                answers[questionId] = parseInt(selectedOption.value, 10);
            }
            // Если ответ не выбран, мы не добавляем его в объект answers
        });

        // Отправка данных на сервер
        fetch('/share/quiz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(answers),
        })
        .then(response => {
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                showPopup(true, data.message || 'Ваши ответы успешно отправлены!');
            } else {
                throw new Error(data.message || 'Неизвестная ошибка');
            }
        })
        .catch((error) => {
            console.error('Ошибка:', error);
            showPopup(false, 'Произошла ошибка при отправке ответов: ' + error.message);
        });
    });
});