/* NEPSE Sathi — Main JavaScript */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Navbar scroll behaviour ──────────────────────── */
  /* ── Navbar scroll behaviour ──────────────────────── */
// const navbar    = document.getElementById('navbar');
// const navbarBg  = document.getElementById('navbar-bg');

// const onScroll = () => {
//   if (window.scrollY > 20) {
//     navbarBg.classList.add('scrolled');
//   } else {
//     navbarBg.classList.remove('scrolled');
//   }
// };
// window.addEventListener('scroll', onScroll, { passive: true });



  /* ── Mobile menu ───────────────────────────────────── */
  const mobileBtn   = document.getElementById('mobile-menu-btn');
  const mobileMenu  = document.getElementById('mobile-menu');
  const iconMenu    = document.getElementById('icon-menu');
  const iconClose   = document.getElementById('icon-close');

  if (mobileBtn) {
    mobileBtn.addEventListener('click', () => {
      const open = !mobileMenu.classList.contains('hidden');
      mobileMenu.classList.toggle('hidden', open);
      iconMenu.classList.toggle('hidden', !open);
      iconClose.classList.toggle('hidden', open);
    });
  }

  /* ── Dark / Light theme toggle ─────────────────────── */
  const themeBtn  = document.getElementById('theme-toggle');
  const iconMoon  = document.getElementById('icon-moon');
  const iconSun   = document.getElementById('icon-sun');
  const html      = document.documentElement;

  const applyTheme = (theme) => {
    if (theme === 'light') {
      html.classList.remove('dark');
      html.classList.add('light');
      iconMoon?.classList.add('hidden');
      iconSun?.classList.remove('hidden');
    } else {
      html.classList.remove('light');
      html.classList.add('dark');
      iconMoon?.classList.remove('hidden');
      iconSun?.classList.add('hidden');
    }
    localStorage.setItem('nepse-theme', theme);
  };

  // Load saved theme
 applyTheme('light');
localStorage.setItem('nepse-theme', 'light');


  themeBtn?.addEventListener('click', () => {
    const current = html.classList.contains('light') ? 'light' : 'dark';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  });

  /* ── Scroll reveal ─────────────────────────────────── */
  const reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(el => revealObserver.observe(el));
  } else {
    reveals.forEach(el => el.classList.add('visible'));
  }

  /* ── Animated number counters ──────────────────────── */
  const counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    const countObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const el  = entry.target;
        const end = parseInt(el.dataset.count, 10);
        const dur = 1600;
        const step = 16;
        const inc  = end / (dur / step);
        let cur    = 0;
        const timer = setInterval(() => {
          cur += inc;
          if (cur >= end) { cur = end; clearInterval(timer); }
          el.textContent = Math.floor(cur).toLocaleString() + (el.dataset.suffix || '');
        }, step);
        countObserver.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach(el => countObserver.observe(el));
  }

  /* ── Mini sparkline canvas charts ─────────────────── */
  const sparklines = document.querySelectorAll('canvas[data-sparkline]');
  sparklines.forEach(canvas => {
    const raw  = canvas.dataset.sparkline.split(',').map(Number);
    const gain = canvas.dataset.gain !== 'false';
    const ctx  = canvas.getContext('2d');
    const W    = canvas.width;
    const H    = canvas.height;
    const min  = Math.min(...raw);
    const max  = Math.max(...raw);
    const range = max - min || 1;
    const pad   = 4;

    const pts = raw.map((v, i) => ({
      x: pad + (i / (raw.length - 1)) * (W - pad * 2),
      y: H - pad - ((v - min) / range) * (H - pad * 2),
    }));

    ctx.clearRect(0, 0, W, H);

    // Fill gradient
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    const color = gain ? '34,197,94' : '239,68,68';
    grad.addColorStop(0, `rgba(${color},0.3)`);
    grad.addColorStop(1, `rgba(${color},0)`);

    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    pts.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(pts[pts.length - 1].x, H);
    ctx.lineTo(pts[0].x, H);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    pts.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = gain ? '#22C55E' : '#EF4444';
    ctx.lineWidth   = 2;
    ctx.lineJoin    = 'round';
    ctx.stroke();
  });

  /* ── Hero dashboard card live flicker ─────────────── */
  const liveEl = document.querySelector('.live-value');
  if (liveEl) {
    setInterval(() => {
      const delta = (Math.random() - 0.48) * 2;
      const cur   = parseFloat(liveEl.textContent.replace(',', '')) + delta;
      liveEl.textContent = cur.toFixed(2);
      liveEl.style.color = delta >= 0 ? '#22C55E' : '#EF4444';
      setTimeout(() => { liveEl.style.color = ''; }, 300);
    }, 2000);
  }

});
