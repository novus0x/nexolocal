const authContent = document.getElementById('auth-content');
const toggleText = document.getElementById('toggle-text');
const socialAuth = document.getElementById('social-auth');

function render_login() {
    authContent.classList.remove('fade-in');
    void authContent.offsetWidth;
    authContent.classList.add('fade-in');
    socialAuth.style.display = 'block';

    authContent.innerHTML = `
                <div id="login-form">
                    <h2 class="text-2xl font-bold mb-1">Bienvenido</h2>
                    <p class="text-gray-500 text-sm mb-8">Accede a tu panel de control comercial.</p>

                    <form action="/auth/login" method="POST" class="space-y-5" autocomplete="off">
                        <div class="space-y-2">
                            <label class="block text-[10px] font-bold uppercase tracking-[0.15em] text-gray-400 ml-1">Correo Electrónico</label>
                            <input type="email" name="email" required placeholder="youremail@gmail.com" class="input-field w-full px-4 py-3.5 rounded-xl text-sm text-white placeholder-gray-600" autofocus>
                        </div>

                        <div class="space-y-2">
                            <div class="flex justify-between items-center ml-1">
                                <label class="block text-[10px] font-bold uppercase tracking-[0.15em] text-gray-400">Contraseña</label>
                            </div>
                            <input type="password" name="password" required placeholder="••••••••" class="input-field w-full px-4 py-3.5 rounded-xl text-sm text-white placeholder-gray-600">
                        </div>

                        <div class="flex items-center justify-between py-2">
                            <label class="flex items-center gap-3 cursor-pointer group">
                                <input type="checkbox" name="expire" value="true" class="custom-checkbox">
                                <span class="text-xs text-gray-400 group-hover:text-gray-200 transition-colors">Mantener sesión iniciada</span>
                            </label>
                            <button type="button" onclick="render_forgot_password()" class="text-[10px] font-bold text-[#FD420A] hover:underline uppercase tracking-wider cursor-pointer">¿Olvidaste la clave?</button>
                        </div>

                        <button type="submit" class="w-full bg-[#FD420A] hover:bg-[#E33A08] text-white py-4 rounded-2xl font-bold text-sm transition-all shadow-lg shadow-orange-900/20 active:scale-[0.98] mt-4 cursor-pointer">
                            Entrar al Sistema
                        </button>
                    </form>
                </div>
            `;
    toggleText.innerHTML = `¿No tienes una cuenta? <button onclick="render_register()" class="text-[#FD420A] font-bold hover:underline">Regístrate ahora</button>`;
}

function render_register() {
    authContent.classList.remove('fade-in');
    void authContent.offsetWidth;
    authContent.classList.add('fade-in');
    socialAuth.style.display = 'block';

    authContent.innerHTML = `
                <div id="register-form">
                    <h2 class="text-2xl font-bold mb-1">Nueva Cuenta</h2>
                    <p class="text-gray-500 text-sm mb-8">Completa tus datos para empezar.</p>

                    <form action="/auth/register" method="POST" class="space-y-4" autocomplete="off">
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div class="space-y-2">
                                <label class="block text-[10px] font-bold uppercase tracking-widest text-gray-400 ml-1">Username</label>
                                <input type="text" name="username" required placeholder="username" class="input-field w-full px-4 py-3 rounded-xl text-sm text-white" autofocus>
                            </div>
                            <div class="space-y-2">
                                <label class="block text-[10px] font-bold uppercase tracking-widest text-gray-400 ml-1">Fecha Nacimiento</label>
                                <input type="date" name="birth" required class="input-field w-full px-4 py-3 rounded-xl text-sm text-white">
                            </div>
                        </div>

                        <div class="space-y-2">
                            <label class="block text-[10px] font-bold uppercase tracking-widest text-gray-400 ml-1">Nombre Completo</label>
                            <input type="text" name="fullname" required placeholder="Ej. Alex Martinez" class="input-field w-full px-4 py-3 rounded-xl text-sm text-white">
                        </div>

                        <div class="space-y-2">
                            <label class="block text-[10px] font-bold uppercase tracking-widest text-gray-400 ml-1">Email</label>
                            <input type="email" name="email" required placeholder="youremail@gmail.com" class="input-field w-full px-4 py-3 rounded-xl text-sm text-white">
                        </div>

                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div class="space-y-2">
                                <label class="block text-[10px] font-bold uppercase tracking-widest text-gray-400 ml-1">Contraseña</label>
                                <input type="password" name="password" required placeholder="••••••••" class="input-field w-full px-4 py-3 rounded-xl text-sm text-white">
                            </div>
                            <div class="space-y-2">
                                <label class="block text-[10px] font-bold uppercase tracking-widest text-gray-400 ml-1">Confirmar</label>
                                <input type="password" name="confirm_password" required placeholder="••••••••" class="input-field w-full px-4 py-3 rounded-xl text-sm text-white">
                            </div>
                        </div>

                        <button type="submit" class="w-full bg-[#FD420A] hover:bg-[#E33A08] text-white py-4 rounded-2xl font-bold text-sm transition-all shadow-lg shadow-orange-900/20 active:scale-[0.98] mt-4 cursor-pointer">
                            Crear mi Cuenta
                        </button>
                    </form>
                </div>
            `;
    toggleText.innerHTML = `¿Ya eres miembro? <button onclick="render_login()" class="text-[#FD420A] font-bold hover:underline">Inicia sesión</button>`;
}

function render_forgot_password() {
    authContent.classList.remove('fade-in');
    void authContent.offsetWidth;
    authContent.classList.add('fade-in');
    socialAuth.style.display = 'none';

    authContent.innerHTML = `
                <div id="forgot-password-form">
                    <h2 class="text-2xl font-bold mb-1">Recuperar Clave</h2>
                    <p class="text-gray-500 text-sm mb-8">Ingresa tu correo para enviarte las instrucciones de restablecimiento.</p>

                    <form action="/auth/forgot-password" method="POST" class="space-y-5" autocomplete="off">
                        <div class="space-y-2">
                            <label class="block text-[10px] font-bold uppercase tracking-[0.15em] text-gray-400 ml-1">Correo Electrónico</label>
                            <input type="email" name="email" required placeholder="email@ejemplo.com" class="input-field w-full px-4 py-3.5 rounded-xl text-sm text-white placeholder-gray-600" autofocus>
                        </div>

                        <button type="submit" class="w-full bg-[#FD420A] hover:bg-[#E33A08] text-white py-4 rounded-2xl font-bold text-sm transition-all shadow-lg shadow-orange-900/20 active:scale-[0.98] mt-4 cursor-pointer">
                            Enviar Instrucciones
                        </button>
                        
                        <button type="button" onclick="render_login()" class="w-full text-center text-xs text-gray-500 hover:text-white transition-colors mt-2 font-medium cursor-pointer">
                            Volver al inicio de sesión
                        </button>
                    </form>
                </div>
            `;
    toggleText.innerHTML = ``;
}
