// Landbot.ia con Burbuja Dinámica
window.addEventListener('mouseover', initLandbot, { once: true });
window.addEventListener('touchstart', initLandbot, { once: true });
var myLandbot;

// Configuración de movimiento dinámico
const chatbotConfig = {
  positions: [
    { bottom: '20px', right: '20px' },    // Esquina inferior derecha
    { bottom: '20px', left: '20px' },     // Esquina inferior izquierda
    { top: '20px', right: '20px' },       // Esquina superior derecha
    { top: '20px', left: '20px' },        // Esquina superior izquierda
    { bottom: '50%', right: '20px' },     // Centro derecha
    { bottom: '50%', left: '20px' },      // Centro izquierda
    { top: '50%', right: '20px' },        // Centro superior derecha
    { bottom: '20px', right: '50%' }      // Centro inferior
  ],
  currentPosition: 0,
  moveInterval: 5000, // Cambiar posición cada 5 segundos (más rápido)
  animationDuration: '1.2s',
  isFloating: false,
  floatingSpeed: 2
};

function initLandbot() {
  if (!myLandbot) {
    var s = document.createElement('script');
    s.type = "module"
    s.async = true;
    s.addEventListener('load', function() {
      myLandbot = new Landbot.Livechat({
        configUrl: 'https://storage.googleapis.com/landbot.online/v3/H-3156682-MGTV461TDNMJ4FB7/index.json',
      });
      
      // Inicializar movimiento dinámico después de que se cargue el chatbot
      setTimeout(() => {
        initDynamicMovement();
      }, 2000);
    });
    s.src = 'https://cdn.landbot.io/landbot-3/landbot-3.0.0.mjs';
    var x = document.getElementsByTagName('script')[0];
    x.parentNode.insertBefore(s, x);
  }
}

function initDynamicMovement() {
  // Crear estilos CSS dinámicos para el chatbot
  const style = document.createElement('style');
  style.textContent = `
    /* Estilos para burbuja dinámica de Landbot */

      landbot-launcher {
      transition: all ${chatbotConfig.animationDuration} cubic-bezier(0.4, 0, 0.2, 1) !important;
      z-index: 999999 !important;
      position: fixed !important;
    }
    
    #landbot-launcher:hover {
      transform: scale(1.15) rotate(5deg) !important;
      transition: transform 0.3s ease !important;
      box-shadow: 0 8px 25px rgba(224, 140, 43, 0.4) !important;
    }
    
    /* Animación de pulso más llamativa */
    @keyframes chatbot-pulse {
      0% { 
        box-shadow: 0 0 0 0 rgba(224, 140, 43, 0.8);
        transform: scale(1);
      }
      50% {
        box-shadow: 0 0 0 15px rgba(224, 140, 43, 0);
        transform: scale(1.05);
      }
      100% {
        box-shadow: 0 0 0 0 rgba(224, 140, 43, 0);
        transform: scale(1);
      }
    }
    
    /* Animación de flotación */
    @keyframes chatbot-float {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-8px);
      }
    }
    
    /* Animación de rebote lateral */
    @keyframes chatbot-bounce {
      0%, 100% {
        transform: translateX(0) scale(1);
      }
      25% {
        transform: translateX(-5px) scale(1.02);
      }
      75% {
        transform: translateX(5px) scale(1.02);
      }
    }
    
    #landbot-launcher {
      animation: 
        chatbot-pulse 4s infinite,
        chatbot-float 3s ease-in-out infinite,
        chatbot-bounce 6s ease-in-out infinite !important;
    }
    
    /* Efecto de entrada más dramático */
    .chatbot-entrance {
      animation: chatbot-entrance 1.2s ease-out !important;
    }
    
    @keyframes chatbot-entrance {
      0% {
        opacity: 0;
        transform: scale(0.3) translateY(100px) rotate(180deg);
      }
      60% {
        opacity: 1;
        transform: scale(1.1) translateY(-10px) rotate(-10deg);
      }
      100% {
        opacity: 1;
        transform: scale(1) translateY(0) rotate(0deg);
      }
    }
    
    /* Efecto de cambio de posición */
    .chatbot-moving {
      animation: chatbot-moving-effect 0.8s ease-in-out !important;
    }
    
    @keyframes chatbot-moving-effect {
      0% {
        transform: scale(1) rotate(0deg);
      }
      50% {
        transform: scale(0.8) rotate(360deg);
        opacity: 0.7;
      }
      100% {
        transform: scale(1) rotate(0deg);
      }
    }
  `;
  document.head.appendChild(style);
  
  // Función para mover el chatbot con efecto visual
  function moveChatbot() {
    const launcher = document.getElementById('landbot-launcher');
    if (launcher) {
      // Agregar clase de movimiento
      launcher.classList.add('chatbot-moving');
      
      setTimeout(() => {
        const newPosition = chatbotConfig.positions[chatbotConfig.currentPosition];
        
        // Limpiar posiciones anteriores
        launcher.style.top = 'auto';
        launcher.style.bottom = 'auto';
        launcher.style.left = 'auto';
        launcher.style.right = 'auto';
        
        // Aplicar nueva posición
        Object.keys(newPosition).forEach(key => {
          launcher.style[key] = newPosition[key];
        });
        
        // Siguiente posición
        chatbotConfig.currentPosition = (chatbotConfig.currentPosition + 1) % chatbotConfig.positions.length;
        
        // Remover clase de movimiento
        setTimeout(() => {
          launcher.classList.remove('chatbot-moving');
        }, 800);
      }, 400);
    }
  }
  
  // Función para movimiento aleatorio más agresivo
  function moveToRandomPosition() {
    const launcher = document.getElementById('landbot-launcher');
    if (launcher) {
      // Generar posición completamente aleatoria
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const launcherSize = 60; // Tamaño aproximado del launcher
      
      const randomPositions = [
        // Esquinas con variación
        { top: '20px', right: '20px' },
        { top: '20px', left: '20px' },
        { bottom: '20px', right: '20px' },
        { bottom: '20px', left: '20px' },
        // Posiciones centrales
        { top: '50%', right: '20px' },
        { top: '50%', left: '20px' },
        { bottom: '50%', right: '20px' },
        { bottom: '50%', left: '20px' },
        // Posiciones centrales horizontales
        { top: '20px', left: '50%' },
        { bottom: '20px', left: '50%' },
        // Centro absoluto (temporal)
        { top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }
      ];
      
      const randomIndex = Math.floor(Math.random() * randomPositions.length);
      const newPosition = randomPositions[randomIndex];
      
      launcher.classList.add('chatbot-moving');
      
      setTimeout(() => {
        // Limpiar posiciones anteriores
        launcher.style.top = 'auto';
        launcher.style.bottom = 'auto';
        launcher.style.left = 'auto';
        launcher.style.right = 'auto';
        launcher.style.transform = '';
        
        // Aplicar nueva posición
        Object.keys(newPosition).forEach(key => {
          launcher.style[key] = newPosition[key];
        });
        
        setTimeout(() => {
          launcher.classList.remove('chatbot-moving');
        }, 800);
      }, 400);
    }
  }
  
  // Función para detectar si el chat está abierto
  function isChatOpen() {
    const chatWindow = document.querySelector('#landbot-iframe, .landbot-chat-window, [class*="landbot"][class*="open"]');
    return chatWindow && chatWindow.style.display !== 'none';
  }
  
  // Iniciar movimiento automático más agresivo
  const moveInterval = setInterval(() => {
    if (!isChatOpen()) {
      // Alternar entre movimiento predefinido y aleatorio
      if (Math.random() > 0.5) {
        moveToRandomPosition();
      } else {
        moveChatbot();
      }
    }
  }, chatbotConfig.moveInterval);
  
  // Agregar movimiento adicional con scroll
  let lastScrollPosition = window.pageYOffset;
  let scrollTimeout;
  
  window.addEventListener('scroll', () => {
    const launcher = document.getElementById('landbot-launcher');
    if (launcher && !isChatOpen()) {
      const currentScrollPosition = window.pageYOffset;
      const scrollDifference = Math.abs(currentScrollPosition - lastScrollPosition);
      
      // Si el usuario hace scroll significativo, mover el chatbot
      if (scrollDifference > 100) {
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
          moveToRandomPosition();
          lastScrollPosition = currentScrollPosition;
        }, 500);
      }
    }
  });
  
  // Agregar funcionalidad de pausa al hacer hover
  setTimeout(() => {
    const launcher = document.getElementById('landbot-launcher');
    if (launcher) {
      launcher.classList.add('chatbot-entrance');
      
      let pauseMovement = false;
      
      launcher.addEventListener('mouseenter', () => {
        pauseMovement = true;
        launcher.style.animationPlayState = 'paused';
      });
      
      launcher.addEventListener('mouseleave', () => {
        pauseMovement = false;
        launcher.style.animationPlayState = 'running';
      });
      
      // Detener movimiento cuando el chat esté abierto
      const observer = new MutationObserver(() => {
        if (isChatOpen()) {
          clearInterval(moveInterval);
        }
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true
      });
    }
  }, 1000);
}

// Función para personalizar la posición manualmente (opcional)
window.setChatbotPosition = function(position) {
  const launcher = document.getElementById('landbot-launcher');
  if (launcher && chatbotConfig.positions[position]) {
    const newPos = chatbotConfig.positions[position];
    
    launcher.style.top = 'auto';
    launcher.style.bottom = 'auto';
    launcher.style.left = 'auto';
    launcher.style.right = 'auto';
    
    Object.keys(newPos).forEach(key => {
      launcher.style[key] = newPos[key];
    });
    
    chatbotConfig.currentPosition = position;
  }
};

// Función para pausar/reanudar el movimiento automático
window.toggleChatbotMovement = function(pause = null) {
  const launcher = document.getElementById('landbot-launcher');
  if (launcher) {
    if (pause === null) {
      // Toggle
      const isPaused = launcher.style.animationPlayState === 'paused';
      launcher.style.animationPlayState = isPaused ? 'running' : 'paused';
    } else {
      launcher.style.animationPlayState = pause ? 'paused' : 'running';
    }
  }
};
