const form = document.getElementById('loginForm');
const message = document.getElementById('message');

form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            credentials: 'include', // важно для cookie refresh_token
            body: new URLSearchParams({
                username: username,
                password: password
            })
        });

        if (!response.ok) {
            throw new Error('Ошибка авторизации');
        }

        const data = await response.json();

        // Сохраняем access_token (например, в памяти или localStorage)
        localStorage.setItem('access_token', data.access_token);

        // CSRF токен тоже пригодится
        localStorage.setItem('csrf_token', data.csrf_token);

        message.style.color = "lightgreen";
        message.textContent = "Успешный вход";

        // переход дальше
        setTimeout(() => {
            window.location.href = "/";
        }, 500);

    } catch (error) {
        message.style.color = "red";
        message.textContent = "Неверный логин или пароль";
    }
});