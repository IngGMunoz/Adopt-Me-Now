// Asistente virtual (Landbot) dentro de un panel propio de la app (#chatPanel).
// Landbot se incrusta en modo Container y su script solo se descarga la primera vez que se abre.
(function () {
  'use strict';

  const CONFIG_URL = 'https://storage.googleapis.com/landbot.online/v3/H-3156682-MGTV461TDNMJ4FB7/index.json';
  const SCRIPT_URL = 'https://cdn.landbot.io/landbot-3/landbot-3.0.0.mjs';
  const boton = document.getElementById('chatLauncher');
  const panel = document.getElementById('chatPanel');
  if (!boton || !panel) return;
  const icono = boton.querySelector('i');
  let cargado = false;

  // El panel ya tiene su encabezado: se oculta el de Landbot (mismo origen, iframe sin src)
  function ocultarEncabezadoLandbot() {
    const doc = panel.querySelector('iframe')?.contentDocument;
    if (!doc) return;
    const estilo = doc.createElement('style');
    estilo.textContent = '.Header { display: none !important; }';
    doc.head.appendChild(estilo);
  }

  function cargar() {
    cargado = true;
    const s = document.createElement('script');
    s.type = 'module';
    s.src = SCRIPT_URL;
    s.addEventListener('load', function () {
      const bot = new window.Landbot.Container({ container: '#chatBot', configUrl: CONFIG_URL });
      bot.onLoad(function () {
        ocultarEncabezadoLandbot();
        panel.querySelector('.chat-panel__loading')?.remove();
      });
    });
    s.addEventListener('error', function () {
      cargado = false;
      s.remove();
      panel.querySelector('.chat-panel__loading').textContent = 'No se pudo cargar el asistente. Intenta de nuevo más tarde.';
    });
    document.head.appendChild(s);
  }

  function mostrar(abierto) {
    panel.hidden = !abierto;
    boton.setAttribute('aria-expanded', String(abierto));
    boton.setAttribute('aria-label', abierto ? 'Cerrar el asistente' : 'Abrir el asistente de adopción');
    icono.className = abierto ? 'fa-solid fa-xmark' : 'fa-solid fa-comment-dots';
    if (abierto && !cargado) cargar();
  }

  boton.addEventListener('click', function () { mostrar(panel.hidden); });
  panel.querySelector('.chat-panel__close').addEventListener('click', function () {
    mostrar(false);
    boton.focus();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !panel.hidden) {
      mostrar(false);
      boton.focus();
    }
  });
})();
