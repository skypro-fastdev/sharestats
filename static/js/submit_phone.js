document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('phoneForm');
    const popup = document.getElementById('successPopup');

    form.addEventListener('submit', function (e) {
        e.preventDefault();

        const phoneNumber = document.getElementById('phoneNumber').value;
        const countryCode = window.iti.getSelectedCountryData().dialCode;
        const studentId = document.getElementById('studentId').value;

        fetch('/share/submit-phone', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone: '+' + countryCode + '-' + phoneNumber,
                student_id: studentId,
            }),
        })
            .then(response => response.json())
            .then(data => {
                popup.style.display = 'block';
                setTimeout(() => {
                    popup.style.display = 'none';
                }, 4000);
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    });
});
