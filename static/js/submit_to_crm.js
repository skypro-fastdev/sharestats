document.addEventListener('DOMContentLoaded', function () {
    const phoneForm1 = document.getElementById('phoneForm1');
    const phoneForm2 = document.getElementById('phoneForm2');
    const phoneInput1 = document.getElementById('phoneNumber1');
    const phoneInput2 = document.getElementById('phoneNumber2');
    const chooseCourseButton = document.getElementById('choose-course');
    const studentId = document.getElementById('studentId').value;
    const popup = document.getElementById('successPopup');
    const successImagePath = popup.dataset.successImage;
    const errorImagePath = popup.dataset.errorImage;
    const popupMessage = document.getElementById('popupMessage');
    const popupImage = document.getElementById('popupImage');
    const popupTitle = document.getElementById('popupTitle');

    let isSyncing = false;

    function syncPhoneInputs(sourceInput, targetInput, sourceIti, targetIti) {
        if (isSyncing) return;
        isSyncing = true;
        const number = sourceIti.a.value;
        targetIti.setNumber(number);
        isSyncing = false;
    }

    function isValidPhoneNumber(phoneNumber) {
        const phoneRegex = /^[\d-]{9,20}$/;
        return phoneRegex.test(phoneNumber) && phoneNumber.replace(/-/g, '').length >= 9;
    }

    // Синхронизация при вводе
    phoneInput1.addEventListener('input', () => syncPhoneInputs(phoneInput1, phoneInput2, window.iti1, window.iti2));
    phoneInput2.addEventListener('input', () => syncPhoneInputs(phoneInput2, phoneInput1, window.iti2, window.iti1));

    // Синхронизация при изменении страны
    phoneInput1.addEventListener('countrychange', () => syncPhoneInputs(phoneInput1, phoneInput2, window.iti1, window.iti2));
    phoneInput2.addEventListener('countrychange', () => syncPhoneInputs(phoneInput2, phoneInput1, window.iti2, window.iti1));

    function showPopup(message, isSuccess = true) {
        popupMessage.innerHTML = message;
        popupTitle.textContent = isSuccess ? 'Готово!' : 'Ошибка';
        popupImage.src = isSuccess ? successImagePath : errorImagePath;
        popupImage.alt = isSuccess ? 'Успешно' : 'Ошибка';
        popup.style.display = 'block';
        setTimeout(() => {
            popup.style.display = 'none';
        }, 3000);
    }

    function submitForm(data, successMessage, metrikaEvent) {
        fetch('/share/submit-to-crm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    showPopup(successMessage, true);
                    // Отправляем событие в Яндекс.Метрику
                    if (typeof ym !== 'undefined') {
                        ym(97943495, 'reachGoal', metrikaEvent);
                    }
                } else {
                    showPopup(data.message || 'Произошла ошибка. Пожалуйста, попробуйте еще раз.', false);
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                showPopup('Произошла ошибка. Пожалуйста, попробуйте еще раз.', false);
            });
    }

    function handleSubmit(e, iti, formName) {
        e.preventDefault();

        const phoneNumber = iti.a.value;
        const countryCode = iti.getSelectedCountryData().dialCode;

        if (!isValidPhoneNumber(phoneNumber)) {
            showPopup('Пожалуйста, введите корректный номер телефона<br>(может содержать только цифры и тире)', false);
            return;
        }

        let successMessage = 'Мы получили вашу заявку!<br>';
        let order;
        let metrikaEvent;

        if (formName === 'phoneForm1') {
            successMessage += 'Скоро мы вам позвоним или напишем!';
            order = 'consultation';
            metrikaEvent = 'guest_order_kk';
        } else {
            successMessage += 'Скоро мы пришлём вам доступ к мини-курсу!';
            order = 'mini-course';
            metrikaEvent = 'guest_order_minicourse';
        }

        submitForm({
            phone: '+' + countryCode + '-' + phoneNumber,
            student_id: studentId,
            order: order
        }, successMessage, metrikaEvent);
    }

    if (phoneForm1) {
        phoneForm1.addEventListener('submit', (e) => handleSubmit(e, window.iti1, 'phoneForm1'));
    }

    if (phoneForm2) {
        phoneForm2.addEventListener('submit', (e) => handleSubmit(e, window.iti2, 'phoneForm2'));
    }

    if (chooseCourseButton) {
        chooseCourseButton.addEventListener('click', function (e) {
            e.preventDefault();
            const url = `https://sky.pro/courses/referral?utm_source=sharingstats&utm_medium=referral&utm_content=${studentId}&utm_campaign=viral`;
            window.open(url, '_blank');
        });
    }
});