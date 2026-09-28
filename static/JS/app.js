/* Adopt Me · comportamiento compartido por todas las páginas */
(function () {
    'use strict';

    const $ = (sel, root = document) => root.querySelector(sel);
    const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

    // Token CSRF en toda petición fetch que modifica datos (ver Config/auth.py)
    const csrf = $('meta[name="csrf-token"]')?.content;
    const nativeFetch = window.fetch.bind(window);
    window.fetch = (url, opts = {}) => {
        if (csrf && !['GET', 'HEAD'].includes((opts.method || 'GET').toUpperCase())) {
            opts.headers = { ...opts.headers, 'X-CSRF-Token': csrf };
        }
        return nativeFetch(url, opts);
    };

    /* ---------- Menú móvil ---------- */
    function initNav() {
        const toggle = $('.nav-toggle');
        const nav = $('#site-nav');
        if (!toggle || !nav) return;

        const setOpen = (open) => {
            nav.classList.toggle('is-open', open);
            toggle.setAttribute('aria-expanded', String(open));
            toggle.innerHTML = open ? '<i class="fa-solid fa-xmark"></i>' : '<i class="fa-solid fa-bars"></i>';
        };
        toggle.addEventListener('click', () => setOpen(!nav.classList.contains('is-open')));
        document.addEventListener('keydown', (e) => e.key === 'Escape' && setOpen(false));
        window.matchMedia('(min-width: 981px)').addEventListener('change', () => setOpen(false));
    }

    /* ---------- Menú desplegable de usuario ---------- */
    function initUserMenu() {
        const menu = $('.user-menu');
        if (!menu) return;
        const button = $('.user-chip', menu);
        const panel = $('.user-menu__panel', menu);
        const items = () => $$('.user-menu__item', panel);

        const setOpen = (open, focusFirst = false) => {
            panel.hidden = !open;
            button.setAttribute('aria-expanded', String(open));
            // Los avisos flotantes quedarían encima del menú: se cierran al abrirlo
            if (open) $$('.toast').forEach(dismissToast);
            if (open && focusFirst) items()[0]?.focus();
        };

        button.addEventListener('click', () => setOpen(panel.hidden));
        button.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setOpen(true, true);
            }
        });
        // Navegación con flechas dentro del menú; Escape lo cierra y devuelve el foco
        panel.addEventListener('keydown', (e) => {
            const list = items();
            const i = list.indexOf(document.activeElement);
            if (e.key === 'ArrowDown') { e.preventDefault(); list[(i + 1) % list.length].focus(); }
            if (e.key === 'ArrowUp') { e.preventDefault(); list[(i - 1 + list.length) % list.length].focus(); }
            if (e.key === 'Escape') { setOpen(false); button.focus(); }
        });
        // Cerrar al hacer clic fuera, al elegir una opción o al salir del menú con Tab
        document.addEventListener('click', (e) => {
            if (!menu.contains(e.target)) setOpen(false);
        });
        panel.addEventListener('click', (e) => e.target.closest('a') && setOpen(false));
        menu.addEventListener('focusout', (e) => {
            if (e.relatedTarget && !menu.contains(e.relatedTarget)) setOpen(false);
        });
    }

    /* ---------- Avisos (toasts) ---------- */
    const TOAST_ICONS = {
        success: 'fa-circle-check',
        error: 'fa-circle-exclamation',
        warning: 'fa-circle-exclamation',
        info: 'fa-circle-info',
    };

    function dismissToast(toast) {
        if (!toast || toast.classList.contains('is-leaving')) return;
        toast.classList.add('is-leaving');
        setTimeout(() => toast.remove(), 250);
    }

    function wireToast(toast) {
        const close = $('.toast__close', toast);
        if (close) close.addEventListener('click', () => dismissToast(toast));
        // Los errores se quedan hasta que el usuario los cierre
        if (!toast.classList.contains('toast--error')) {
            setTimeout(() => dismissToast(toast), 5000);
        }
    }

    function toast(message, category = 'info') {
        let stack = $('.toast-stack');
        if (!stack) {
            stack = document.createElement('div');
            stack.className = 'toast-stack';
            stack.setAttribute('role', 'status');
            stack.setAttribute('aria-live', 'polite');
            document.body.appendChild(stack);
        }
        const el = document.createElement('div');
        el.className = `toast toast--${category}`;
        const icon = document.createElement('i');
        icon.className = `toast__icon fa-solid ${TOAST_ICONS[category] || TOAST_ICONS.info}`;
        const text = document.createElement('p');
        text.className = 'toast__message';
        text.textContent = message;
        const close = document.createElement('button');
        close.className = 'toast__close';
        close.type = 'button';
        close.setAttribute('aria-label', 'Cerrar aviso');
        close.innerHTML = '<i class="fa-solid fa-xmark"></i>';
        el.append(icon, text, close);
        stack.appendChild(el);
        wireToast(el);
    }

    /* ---------- Modal "inicia sesión para adoptar" ---------- */
    const AuthModal = {
        lastFocus: null,
        show(petName, event) {
            if (event) event.preventDefault();
            const modal = $('#authModal');
            if (!modal) return false;
            $('#modalPetName', modal).textContent = petName || 'esta mascota';

            // Volver a esta página después de iniciar sesión o registrarse
            const next = encodeURIComponent(window.location.pathname + window.location.search);
            $('#authModalLoginLink', modal).href = '/iniciar-sesion?next=' + next;
            $('#authModalRegisterLink', modal).href = '/registro?next=' + next;

            this.lastFocus = document.activeElement;
            modal.hidden = false;
            document.body.style.overflow = 'hidden';
            $('#authModalLoginLink', modal).focus();
            return false;
        },
        close() {
            const modal = $('#authModal');
            if (!modal || modal.hidden) return;
            modal.hidden = true;
            document.body.style.overflow = '';
            if (this.lastFocus) this.lastFocus.focus();
        },
    };

    function initAuthModal() {
        const modal = $('#authModal');
        if (!modal) return;
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.closest('[data-close-modal]')) AuthModal.close();
        });
        document.addEventListener('keydown', (e) => e.key === 'Escape' && AuthModal.close());
        document.addEventListener('click', (e) => {
            const trigger = e.target.closest('[data-auth-required]');
            if (trigger) AuthModal.show(trigger.dataset.authRequired, e);
        });
    }

    /* ---------- Validación de formularios ---------- */
    const MESSAGES = {
        valueMissing: 'Este campo es obligatorio.',
        typeMismatch: 'Revisa el formato.',
        tooShort: (el) => `Debe tener al menos ${el.minLength} caracteres.`,
        patternMismatch: (el) => el.title || 'El formato no es válido.',
    };

    function fieldOf(input) {
        return input.closest('.field');
    }

    function setFieldError(input, message) {
        const field = fieldOf(input);
        if (!field) return;
        let error = $('.field__error', field);
        if (!error) {
            error = document.createElement('p');
            error.className = 'field__error';
            error.id = `${input.id || input.name}-error`;
            field.appendChild(error);
        }
        error.textContent = message || '';
        field.classList.toggle('is-invalid', Boolean(message));
        field.classList.toggle('is-valid', !message && input.value !== '');
        if (message) {
            input.setAttribute('aria-invalid', 'true');
            input.setAttribute('aria-describedby', error.id);
        } else {
            input.removeAttribute('aria-invalid');
        }
    }

    function validateInput(input) {
        let message = '';
        // Reglas personalizadas: data-match="#otroCampo"
        if (input.dataset.match) {
            const other = $(input.dataset.match);
            if (other && input.value && input.value !== other.value) {
                message = input.dataset.matchMessage || 'Los valores no coinciden.';
            }
        }
        if (!message && !input.validity.valid) {
            const v = input.validity;
            const key = Object.keys(MESSAGES).find((k) => v[k]);
            const m = MESSAGES[key] || input.validationMessage;
            message = typeof m === 'function' ? m(input) : m;
            if (key === 'typeMismatch' && input.type === 'email') message = 'Escribe un correo válido, por ejemplo nombre@correo.com.';
        }
        setFieldError(input, message);
        return !message;
    }

    function validateForm(form) {
        const inputs = $$('input, select, textarea', form).filter((el) => el.type !== 'hidden' && !el.disabled);
        const results = inputs.map(validateInput);
        const firstInvalid = inputs[results.indexOf(false)];
        if (firstInvalid) firstInvalid.focus();
        return !firstInvalid;
    }

    function setLoading(button, loading, text) {
        if (!button) return;
        const label = $('.btn__label', button);
        if (loading) {
            button.dataset.originalText = label ? label.textContent : '';
            if (label && text) label.textContent = text;
        } else if (label && button.dataset.originalText) {
            label.textContent = button.dataset.originalText;
        }
        button.classList.toggle('is-loading', loading);
        button.disabled = loading;
    }

    function initForms() {
        $$('form[data-validate]').forEach((form) => {
            form.noValidate = true;
            $$('input, select, textarea', form).forEach((input) => {
                input.addEventListener('blur', () => input.value && validateInput(input));
                input.addEventListener('input', () => {
                    if (fieldOf(input)?.classList.contains('is-invalid')) validateInput(input);
                });
            });
            form.addEventListener('submit', (e) => {
                if (!validateForm(form) || (form.dataset.confirm && !window.confirm(form.dataset.confirm))) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    return;
                }
                // Envío tradicional: mostrar estado de carga en el botón
                if (!form.dataset.ajax) {
                    const btn = $('[type="submit"]', form);
                    setLoading(btn, true, btn?.dataset.loadingText);
                }
            });
        });

        // Mostrar/ocultar contraseña
        $$('.password-toggle').forEach((btn) => {
            btn.addEventListener('click', () => {
                const input = $('input', btn.closest('.field__control'));
                const show = input.type === 'password';
                input.type = show ? 'text' : 'password';
                btn.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
                btn.innerHTML = show ? '<i class="fa-regular fa-eye-slash"></i>' : '<i class="fa-regular fa-eye"></i>';
            });
        });

        // Medidor de fortaleza de contraseña
        $$('[data-strength]').forEach((input) => {
            const bar = $(input.dataset.strength);
            if (!bar) return;
            input.addEventListener('input', () => {
                const v = input.value;
                let score = 0;
                if (v.length >= 8) score++;
                if (v.length >= 12) score++;
                if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
                if (/[0-9]/.test(v)) score++;
                if (/[^A-Za-z0-9]/.test(v)) score++;
                const pct = v ? Math.max(15, score * 20) : 0;
                bar.style.width = pct + '%';
                bar.style.background = score <= 1 ? 'var(--danger)' : score <= 3 ? 'var(--accent)' : 'var(--success)';
            });
        });
    }

    /* ---------- Pestañas accesibles ([role=tablist]) ---------- */
    // La pestaña activa se guarda en la URL (#seccion) para poder enlazarla y volver a ella.
    function initTabs() {
        $$('[role="tablist"]').forEach((list) => {
            const tabs = $$('[role="tab"]', list);
            const select = (tab, focus = true) => {
                tabs.forEach((t) => {
                    const on = t === tab;
                    t.setAttribute('aria-selected', String(on));
                    t.tabIndex = on ? 0 : -1;
                    document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
                });
                if (focus) tab.focus();
                history.replaceState(null, '', location.pathname + location.search + '#' + tab.id.replace('tab-', ''));
            };
            tabs.forEach((tab, i) => {
                tab.addEventListener('click', () => select(tab));
                tab.addEventListener('keydown', (e) => {
                    if (e.key === 'ArrowRight') select(tabs[(i + 1) % tabs.length]);
                    if (e.key === 'ArrowLeft') select(tabs[(i - 1 + tabs.length) % tabs.length]);
                });
            });
            const fromHash = () => tabs.find((t) => t.id === 'tab-' + location.hash.slice(1));
            const initial = fromHash();
            if (initial) select(initial, false);
            window.addEventListener('hashchange', () => {
                const tab = fromHash();
                if (tab) {
                    select(tab, false);
                    list.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
        // Enlaces internos a una pestaña (p. ej. "Ver configuración")
        document.addEventListener('click', (e) => {
            const link = e.target.closest('[data-open-tab]');
            const tab = link && document.getElementById('tab-' + link.dataset.openTab);
            if (tab) {
                e.preventDefault();
                tab.click();
                tab.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }

    /* ---------- Catálogo: búsqueda, filtros y orden ---------- */
    function initCatalog() {
        const grid = $('[data-catalog]');
        if (!grid) return;
        const search = $('#petSearch');
        const sort = $('#petSort');
        const count = $('#petCount');
        const empty = $('#petEmpty');
        const filters = $$('[data-filter]');
        const cards = $$('.pet-card', grid);
        const original = cards.slice();

        const apply = () => {
            const q = (search?.value || '').trim().toLowerCase();
            let visible = 0;
            cards.forEach((card) => {
                const match = (!q || card.dataset.search.includes(q))
                    && filters.every((f) => !f.value || card.dataset[f.dataset.filter] === f.value);
                card.hidden = !match;
                if (match) visible++;
            });
            const order = sort?.value || 'default';
            const sorted = order === 'default'
                ? original
                : cards.slice().sort((a, b) => a.dataset.name.localeCompare(b.dataset.name, 'es') * (order === 'name-desc' ? -1 : 1));
            sorted.forEach((card) => grid.insertBefore(card, empty));
            if (count) count.textContent = visible;
            if (empty) empty.hidden = visible > 0;
        };
        search?.addEventListener('input', apply);
        sort?.addEventListener('change', apply);
        filters.forEach((f) => f.addEventListener('change', apply));
    }

    document.addEventListener('DOMContentLoaded', () => {
        initNav();
        initUserMenu();
        initAuthModal();
        initForms();
        initCatalog();
        initTabs();
        $$('.toast').forEach(wireToast);
        // Aviso guardado antes de recargar la página (p. ej. acciones del panel)
        try {
            const pending = JSON.parse(sessionStorage.getItem('adoptme:toast') || 'null');
            sessionStorage.removeItem('adoptme:toast');
            if (pending) toast(pending.message, pending.category);
        } catch (e) { /* almacenamiento no disponible */ }
    });

    // API pública para scripts de cada página
    window.AdoptMe = { toast, validateForm, setFieldError, setLoading, AuthModal };
    // Compatibilidad con plantillas antiguas
    window.showAuthModal = (name, e) => AuthModal.show(name, e);
})();
