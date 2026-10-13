/**
 * SDA Codes Web Application Logic
 * LocalStorage state, Steam TOTP timer, drag & drop maFile import, i18n
 */

(function () {
  'use strict';

  const STORAGE_KEY = 'sda_web_accounts';
  const LANG_KEY = 'sda_web_lang';

  // State
  let accounts = [];
  let currentAccountIndex = 0;
  let currentLang = localStorage.getItem(LANG_KEY) || 'ru';
  let timerInterval = null;
  let currentStep = -1;

  // Translations
  const I18N = {
    ru: {
      hero_title: 'Steam Desktop Authenticator <span>Онлайн</span>',
      hero_subtitle: 'Безопасный генератор 2FA кодов Steam Guard из файлов .maFile прямо в вашем браузере. Данные хранятся только локально.',
      badge_local: '100% Локально в браузере',
      badge_oss: 'Открытый исходный код',
      badge_safe: 'Ключи не передаются в сеть',
      app_title: 'SDA Codes Web',
      select_account: 'Выберите аккаунт',
      no_accounts: 'Нет добавленных аккаунтов',
      copy_code_hint: 'Кликните по коду для копирования',
      copied_toast: 'Скопировано в буфер!',
      refresh_in: 'Обновление через',
      sec: 'с',
      add_mafile_btn: '+ Добавить .maFile',
      dropzone_title: 'Перетащите сюда .maFile',
      dropzone_sub: 'или нажмите для выбора файлов на устройстве',
      cors_title: 'Подтверждения обменов и ограничение CORS',
      cors_desc: 'Браузерная политика безопасности CORS блокирует прямые запросы к steamcommunity.com с клиентской стороны без стороннего прокси-сервера. Чтобы не ставить под угрозу безопасность ваших сессий, подтверждения обменов выполняются в нашем десктопном приложении.',
      btn_download_desktop: 'Скачать SDA для Windows',
      btn_github_repo: 'Репозиторий на GitHub',
      features_heading: 'Преимущества веб-версии',
      feat1_title: 'Полная приватность',
      feat1_text: 'Все вычисления производятся через Web Crypto API на вашем устройстве. Никакие секретные ключи или файлы никогда не отправляются на сервер.',
      feat2_title: 'Локальное хранилище',
      feat2_text: 'Загруженные аккаунты сохраняются в localStorage браузера. При следующем открытии страницы коды Guard будут сразу доступны.',
      feat3_title: 'Мобильная адаптивность',
      feat3_text: 'Удобный интерфейс как на смартфонах (iOS / Android), так и на ПК. Быстро получайте Steam Guard коды в один клик.',
      faq_heading: 'Часто задаваемые вопросы (FAQ)',
      faq_q1: 'Безопасно ли загружать .maFile на сайт?',
      faq_a1: 'Да, абсолютно. Веб-приложение работает статически через GitHub Pages. Код полностью открыт, генерация кодов происходит исключительно на стороне вашего браузера без каких-либо обращений к сторонним серверам.',
      faq_q2: 'Что такое .maFile?',
      faq_a2: 'maFile (Mobile Authenticator File) — это файл привязки мобильного аутентификатора Steam, содержащий shared_secret для вычисления одноразовых 2FA кодов Steam Guard.',
      faq_q3: 'Почему нельзя подтверждать трейды с сайта?',
      faq_a3: 'Из-за политики CORS (Cross-Origin Resource Sharing) современные браузеры запрещают веб-страницам отправлять авторизованные запросы к Steam. Для подтверждения трейдов и маркета используйте нашу десктопную версию SDA.',
      faq_q4: 'Сохранятся ли аккаунты после закрытия браузера?',
      faq_a4: 'Да. Аккаунты сохраняются в локальном хранилище браузера (localStorage). Вы можете в любой момент удалить их кнопкой с иконкой корзины.',
      footer_copy: 'SDA Codes Web — Неофициальный веб-клиент Steam Desktop Authenticator.',
      footer_disclaimer: 'Steam и логотип Steam являются товарными знаками Valve Corporation. Данный проект не связан с Valve Corporation.',
      confirm_delete: 'Удалить этот аккаунт из локального хранилища?',
      import_success: 'Успешно импортировано аккаунтов: ',
      import_error: 'Ошибка при чтении файла: '
    },
    en: {
      hero_title: 'Steam Desktop Authenticator <span>Online</span>',
      hero_subtitle: 'Secure in-browser Steam Guard 2FA code generator from .maFile. 100% client-side, keys stored only in localStorage.',
      badge_local: '100% In-Browser & Local',
      badge_oss: 'Open Source',
      badge_safe: 'No Secrets Sent Over Network',
      app_title: 'SDA Codes Web',
      select_account: 'Select account',
      no_accounts: 'No accounts added',
      copy_code_hint: 'Click code to copy to clipboard',
      copied_toast: 'Copied to clipboard!',
      refresh_in: 'Refreshes in',
      sec: 's',
      add_mafile_btn: '+ Add .maFile',
      dropzone_title: 'Drag & Drop .maFile here',
      dropzone_sub: 'or click to browse files from device',
      cors_title: 'Trade Confirmations & CORS Limitation',
      cors_desc: 'Browser CORS security policy prohibits direct authorized requests to steamcommunity.com without a third-party proxy server. To protect your session credentials, trade confirmations are supported exclusively in our standalone Desktop app.',
      btn_download_desktop: 'Download SDA for Windows',
      btn_github_repo: 'GitHub Repository',
      features_heading: 'Key Features',
      feat1_title: 'Zero-Knowledge Privacy',
      feat1_text: 'All cryptographic TOTP calculations run locally via Web Crypto API on your device. No keys or files are ever sent to any remote server.',
      feat2_title: 'Local Storage Persistence',
      feat2_text: 'Imported accounts are securely stored in your browser localStorage. Your 2FA codes are instantly available on return visits.',
      feat3_title: 'Mobile & Desktop Ready',
      feat3_text: 'Fully responsive UI tailored for both iOS/Android mobile browsers and desktop screens. Copy Steam Guard codes in one tap.',
      faq_heading: 'Frequently Asked Questions (FAQ)',
      faq_q1: 'Is it safe to import .maFile here?',
      faq_a1: 'Yes, absolutely. The site is hosted statically on GitHub Pages. The source code is open, and all code generation runs entirely in your browser memory without network telemetry.',
      faq_q2: 'What is a .maFile?',
      faq_a2: 'A .maFile (Mobile Authenticator File) is generated when linking Steam Mobile Authenticator. It contains the shared_secret used to calculate time-based 2FA Steam Guard codes.',
      faq_q3: 'Why cannot trades be confirmed directly on the web?',
      faq_a3: 'Modern browser CORS (Cross-Origin Resource Sharing) blocks cross-origin cookie authentication to Steam. For one-click trade & market confirmations, download our Desktop app.',
      faq_q4: 'Are my accounts saved across browser restarts?',
      faq_a4: 'Yes, your accounts remain in your browser localStorage until you clear site data or click the delete button.',
      footer_copy: 'SDA Codes Web — Unofficial Steam Desktop Authenticator Web Client.',
      footer_disclaimer: 'Steam and the Steam logo are trademarks of Valve Corporation. This project is not affiliated with or endorsed by Valve Corporation.',
      confirm_delete: 'Delete this account from local storage?',
      import_success: 'Successfully imported accounts: ',
      import_error: 'Error reading file: '
    }
  };

  // DOM Elements
  const el = {
    accountSelector: document.getElementById('accountSelector'),
    btnDeleteAccount: document.getElementById('btnDeleteAccount'),
    codeDisplayWrap: document.getElementById('codeDisplayWrap'),
    codeValue: document.getElementById('codeValue'),
    timerChunk: document.getElementById('timerChunk'),
    secondsLeft: document.getElementById('secondsLeft'),
    copyToast: document.getElementById('copyToast'),
    dropzone: document.getElementById('dropzone'),
    fileInput: document.getElementById('fileInput'),
    accountsSection: document.getElementById('accountsSection'),
    btnAddMafile: document.getElementById('btnAddMafile'),
    accountsCount: document.getElementById('accountsCount'),
    langRu: document.getElementById('langRu'),
    langEn: document.getElementById('langEn')
  };

  // Load accounts from storage
  function loadAccounts() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        accounts = JSON.parse(raw);
        if (!Array.isArray(accounts)) accounts = [];
      }
    } catch (e) {
      accounts = [];
    }
  }

  // Save accounts to storage
  function saveAccounts() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(accounts));
    } catch (e) {
      console.error('Failed to save accounts to localStorage:', e);
    }
  }

  // Update UI texts for selected language
  function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem(LANG_KEY, lang);
    const t = I18N[lang] || I18N.ru;

    document.querySelectorAll('[data-i18n]').forEach((node) => {
      const key = node.getAttribute('data-i18n');
      if (t[key]) {
        node.innerHTML = t[key];
      }
    });

    if (el.langRu && el.langEn) {
      el.langRu.classList.toggle('active', lang === 'ru');
      el.langEn.classList.toggle('active', lang === 'en');
    }

    renderAccountSelector();
  }

  // Render Account Selector dropdown
  function renderAccountSelector() {
    const t = I18N[currentLang] || I18N.ru;
    el.accountSelector.innerHTML = '';

    if (accounts.length === 0) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.textContent = t.no_accounts;
      el.accountSelector.appendChild(opt);
      el.accountSelector.disabled = true;
      el.btnDeleteAccount.style.display = 'none';
      el.accountsSection.style.display = 'none';
      el.dropzone.style.display = 'flex';
      el.codeValue.textContent = '-----';
      if (el.accountsCount) el.accountsCount.textContent = '0';
      return;
    }

    el.accountSelector.disabled = false;
    el.btnDeleteAccount.style.display = 'flex';
    el.accountsSection.style.display = 'block';
    el.dropzone.style.display = 'none';

    accounts.forEach((acc, idx) => {
      const opt = document.createElement('option');
      opt.value = String(idx);
      opt.textContent = `${acc.accountName} ${acc.steamId ? '(' + acc.steamId + ')' : ''}`;
      if (idx === currentAccountIndex) {
        opt.selected = true;
      }
      el.accountSelector.appendChild(opt);
    });

    if (el.accountsCount) {
      el.accountsCount.textContent = String(accounts.length);
    }
  }

  // Refresh code display
  async function updateCode() {
    if (accounts.length === 0 || currentAccountIndex < 0 || currentAccountIndex >= accounts.length) {
      el.codeValue.textContent = '-----';
      return;
    }

    const acc = accounts[currentAccountIndex];
    if (!acc || !acc.sharedSecret) {
      el.codeValue.textContent = 'ERR';
      return;
    }

    try {
      const code = await SteamTOTP.generateCode(acc.sharedSecret);
      el.codeValue.textContent = code;
    } catch (e) {
      console.error('TOTP calculation error:', e);
      el.codeValue.textContent = 'ERR';
    }
  }

  // Timer Tick (runs every 500ms for smooth progress)
  function onTick() {
    const now = Math.floor(Date.now() / 1000);
    const step = Math.floor(now / 30);
    const remaining = SteamTOTP.getSecondsRemaining(now);

    el.secondsLeft.textContent = String(remaining);

    // Smooth percentage (0 to 100)
    const ms = Date.now() % 30000;
    const pct = Math.max(0, Math.min(100, ((30000 - ms) / 30000) * 100));
    el.timerChunk.style.width = pct + '%';
    el.timerChunk.classList.toggle('danger', remaining <= 5);

    if (step !== currentStep) {
      currentStep = step;
      updateCode();
    }
  }

  // Copy Code to Clipboard
  function copyCode() {
    const code = el.codeValue.textContent.trim();
    if (!code || code === '-----' || code === 'ERR') return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(code).then(showToast).catch(() => fallbackCopy(code));
    } else {
      fallbackCopy(code);
    }
  }

  function fallbackCopy(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast();
    } catch (e) {
      // Ignore
    }
    document.body.removeChild(ta);
  }

  function showToast() {
    const t = I18N[currentLang] || I18N.ru;
    el.copyToast.textContent = t.copied_toast;
    el.copyToast.classList.add('visible');
    setTimeout(() => {
      el.copyToast.classList.remove('visible');
    }, 1800);
  }

  // Import Files (.maFile)
  function handleFiles(fileList) {
    if (!fileList || fileList.length === 0) return;
    const t = I18N[currentLang] || I18N.ru;
    let imported = 0;
    let errors = [];

    const promises = Array.from(fileList).map((file) => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = function (e) {
          try {
            const parsed = SteamTOTP.parseMaFile(e.target.result, file.name);
            // Replace if exists, else append
            const existingIdx = accounts.findIndex(
              (a) => (a.steamId && a.steamId === parsed.steamId) || a.accountName === parsed.accountName
            );
            if (existingIdx >= 0) {
              accounts[existingIdx] = parsed;
            } else {
              accounts.push(parsed);
            }
            imported++;
          } catch (err) {
            errors.push(`${file.name}: ${err.message}`);
          }
          resolve();
        };
        reader.onerror = function () {
          errors.push(`${file.name}: read error`);
          resolve();
        };
        reader.readAsText(file);
      });
    });

    Promise.all(promises).then(() => {
      if (imported > 0) {
        saveAccounts();
        currentAccountIndex = accounts.length - 1;
        renderAccountSelector();
        updateCode();
      }
      if (errors.length > 0) {
        alert(t.import_error + '\n' + errors.join('\n'));
      }
    });
  }

  // Delete current account
  function deleteCurrentAccount() {
    if (accounts.length === 0) return;
    const t = I18N[currentLang] || I18N.ru;
    const acc = accounts[currentAccountIndex];
    if (!confirm(`${t.confirm_delete} (${acc.accountName})`)) return;

    accounts.splice(currentAccountIndex, 1);
    if (currentAccountIndex >= accounts.length) {
      currentAccountIndex = Math.max(0, accounts.length - 1);
    }
    saveAccounts();
    renderAccountSelector();
    updateCode();
  }

  // Setup Event Listeners
  function initListeners() {
    // Account Selector Change
    el.accountSelector.addEventListener('change', (e) => {
      currentAccountIndex = parseInt(e.target.value, 10) || 0;
      updateCode();
    });

    // Delete Button
    el.btnDeleteAccount.addEventListener('click', deleteCurrentAccount);

    // Code Copy
    el.codeDisplayWrap.addEventListener('click', copyCode);

    // Language switcher
    if (el.langRu) el.langRu.addEventListener('click', () => applyLanguage('ru'));
    if (el.langEn) el.langEn.addEventListener('click', () => applyLanguage('en'));

    // Dropzone & File Input
    const triggerFilePicker = () => el.fileInput.click();
    el.dropzone.addEventListener('click', triggerFilePicker);
    if (el.btnAddMafile) el.btnAddMafile.addEventListener('click', triggerFilePicker);

    el.fileInput.addEventListener('change', (e) => {
      handleFiles(e.target.files);
      el.fileInput.value = '';
    });

    // Drag and drop events
    ['dragenter', 'dragover'].forEach((ev) => {
      el.dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach((ev) => {
      el.dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.dropzone.classList.remove('dragover');
      });
    });

    el.dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer && e.dataTransfer.files) {
        handleFiles(e.dataTransfer.files);
      }
    });

    // FAQ Accordion
    document.querySelectorAll('.faq-question').forEach((btn) => {
      btn.addEventListener('click', () => {
        const item = btn.closest('.faq-item');
        if (item) {
          item.classList.toggle('open');
        }
      });
    });
  }

  // Initialize Application
  function init() {
    loadAccounts();
    applyLanguage(currentLang);
    renderAccountSelector();
    updateCode();
    initListeners();

    // Start ticker
    onTick();
    timerInterval = setInterval(onTick, 500);
  }

  // Boot
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
