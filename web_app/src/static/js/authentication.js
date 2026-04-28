const form = document.getElementById('loginForm');
const message = document.getElementById('message');

form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // сброс состояния
    message.classList.remove("error", "success");
    message.textContent = "";

    try {
        const response = await fetch('/72tldh/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            credentials: 'include',
            body: new URLSearchParams({
                username: username,
                password: password
            })
        });

        if (!response.ok) {
            throw new Error('Ошибка авторизации');
        }

        const data = await response.json();

        // сохраняем токены
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('csrf_token', data.csrf_token);

        // ✅ успех
        message.classList.add("success");
        message.textContent = "Успешный вход";

        setTimeout(() => {
            window.location.href = "/72tldh/";
        }, 500);

    } catch (error) {
        // ❌ ошибка
        message.classList.add("error");
        message.textContent = "Неверный логин или пароль";
    }
});