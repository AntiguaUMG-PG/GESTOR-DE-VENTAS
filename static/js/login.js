document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Login page loaded');
    
    // Recuperar datos guardados
    if (localStorage.getItem('rememberedUser')) {
        document.getElementById('usuarioInput').value = localStorage.getItem('rememberedUser');
        document.getElementById('customCheck').checked = true;
    }

    // Crear partículas de animación
    createParticles();

    // Agregar animaciones UI
    animateUI();
});

// Función para manejar el envío del formulario
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    loginForm.addEventListener('submit', function(e) {
        console.log('📝 Form submitted');
        
        const usuario = document.getElementById('usuarioInput').value.trim();
        const clave = document.getElementById('claveInput').value.trim();

        console.log('🔐 Login attempt:', {
            usuario: usuario,
            password_length: clave.length
        });

        // Validar campos
        if (!usuario || !clave) {
            console.log('❌ Campos vacíos');
            e.preventDefault();
            alert('Por favor complete todos los campos');
            return;
        }

        // Guardar usuario si checkbox está marcado
        if (document.getElementById('customCheck').checked) {
            localStorage.setItem('rememberedUser', usuario);
            console.log('💾 Usuario guardado en localStorage');
        } else {
            localStorage.removeItem('rememberedUser');
        }

        console.log('✅ Formulario válido, enviando...');
        // El formulario se enviará normalmente
    });

    // Toggle visibilidad de contraseña
    const togglePassword = document.createElement('button');
    togglePassword.type = 'button';
    togglePassword.className = 'btn btn-link position-absolute end-0 top-50 translate-middle-y';
    togglePassword.style.zIndex = '10';
    togglePassword.innerHTML = '<i class="fas fa-eye"></i>';
    togglePassword.onclick = function() {
        const input = document.getElementById('claveInput');
        input.type = input.type === 'password' ? 'text' : 'password';
        this.innerHTML = input.type === 'password' ? 
            '<i class="fas fa-eye"></i>' : 
            '<i class="fas fa-eye-slash"></i>';
    };
    document.getElementById('claveInput').parentNode.appendChild(togglePassword);
});

// Animación de partículas
function createParticles() {
    const particles = document.getElementById('particles');
    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 5 + 2;
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;
        const duration = Math.random() * 20 + 10;
        const delay = Math.random() * 5;

        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        particle.style.left = `${posX}%`;
        particle.style.top = `${posY}%`;
        particle.style.animation = `
            float ${duration}s infinite ease-in-out ${delay}s,
            pulse ${duration/2}s infinite ease-in-out ${delay}s
        `;

        particles.appendChild(particle);
    }
}

// Animación de elementos UI
function animateUI() {
    const elements = document.querySelectorAll('.feature-item');
    elements.forEach((el, index) => {
        el.style.animationDelay = `${index * 0.2}s`;
    });
}