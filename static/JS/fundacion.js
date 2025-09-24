// JS para asegurar que el botón "Contactar Fundación" abra la web correctamente

document.addEventListener('DOMContentLoaded', () => {
    const btn = document.querySelector('.cta[href^="http"]');
    if (btn) {
        btn.addEventListener('click', function(e) {
            // Abre el enlace en una nueva pestaña (por si el atributo target fallara)
            window.open(this.href, '_blank', 'noopener');
            e.preventDefault();
        });
    }
});