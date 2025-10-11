window.addEventListener('load', function() {
    const loaderBg = document.querySelector('.loader_bg');
    
    // Espera 3 segundos antes de comenzar a desvanecer el loader
    setTimeout(() => {
        loaderBg.style.opacity = '0';
        
        // Espera 0.5 segundos más (la duración de la transición) antes de ocultar completamente el loader
        setTimeout(() => {
            loaderBg.style.display = 'none';
        }, 500);
    }, 1000);
});