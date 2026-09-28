// Asistente virtual (Landbot). Se carga en la primera interacción del usuario
// para no retrasar la carga inicial de la página.
(function () {
  'use strict';

  const CONFIG_URL = 'https://storage.googleapis.com/landbot.online/v3/H-3156682-MGTV461TDNMJ4FB7/index.json';
  const SCRIPT_URL = 'https://cdn.landbot.io/landbot-3/landbot-3.0.0.mjs';
  let loaded = false;

  function initLandbot() {
    if (loaded) return;
    loaded = true;
    const s = document.createElement('script');
    s.type = 'module';
    s.async = true;
    s.src = SCRIPT_URL;
    s.addEventListener('load', function () {
      window.myLandbot = new window.Landbot.Livechat({ configUrl: CONFIG_URL });
    });
    document.head.appendChild(s);
  }

  ['mouseover', 'touchstart', 'scroll', 'keydown'].forEach(function (evt) {
    window.addEventListener(evt, initLandbot, { once: true, passive: true });
  });
})();
