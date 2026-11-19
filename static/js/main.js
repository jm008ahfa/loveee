/* =========================================================================
   TO MY LOVE — shared interactions
   ========================================================================= */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------- Navigation ---------------- */
  var nav = document.querySelector("[data-nav]");
  var navToggle = document.querySelector("[data-nav-toggle]");
  var body = document.body;
  var isHome = body.classList.contains("page-home");

  function onScroll() {
    if (!nav) return;
    if (window.scrollY > 12) nav.classList.add("is-scrolled");
    else nav.classList.remove("is-scrolled");
  }
  if (nav && !isHome) nav.classList.add("is-solid");
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  function closeNav() {
    body.classList.remove("nav-open");
    if (navToggle) navToggle.setAttribute("aria-expanded", "false");
  }
  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var open = body.classList.toggle("nav-open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    document.querySelectorAll("#navLinks a").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeNav();
    });
  }

  /* ---------------- Reveal on scroll ---------------- */
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if (!("IntersectionObserver" in window) || reduceMotion) {
      revealEls.forEach(function (el) { el.classList.add("is-visible"); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
      revealEls.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---------------- Toasts ---------------- */
  document.querySelectorAll("[data-toast]").forEach(function (toast) {
    var closeBtn = toast.querySelector("[data-toast-close]");
    function dismiss() {
      toast.classList.add("is-leaving");
      setTimeout(function () { toast.remove(); }, 320);
    }
    if (closeBtn) closeBtn.addEventListener("click", dismiss);
    setTimeout(dismiss, 6500);
  });

  /* ---------------- Copy to clipboard ---------------- */
  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (err) { ok = false; }
    area.remove();
    return ok;
  }

  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      if (!text) return;
      var done = function (ok) {
        var original = btn.getAttribute("data-copy-label-original") || btn.textContent.trim();
        btn.setAttribute("data-copy-label-original", original);
        if (btn.classList.contains("icon-button")) {
          var old = btn.innerHTML;
          btn.innerHTML = ok ? "✓" : "!";
          setTimeout(function () { btn.innerHTML = old; }, 1600);
        } else {
          btn.textContent = ok ? "Copied ♥" : "Press Ctrl+C";
          setTimeout(function () { btn.textContent = original; }, 1800);
        }
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done(true); }).catch(function () { done(fallbackCopy(text)); });
      } else {
        done(fallbackCopy(text));
      }
    });
  });

  document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = document.querySelector(btn.getAttribute("data-copy-target"));
      if (!input) return;
      input.select();
      input.setSelectionRange(0, 99999);
      var text = input.value;
      var done = function (ok) {
        var old = btn.textContent;
        btn.textContent = ok ? "Copied ♥" : "Copy failed";
        setTimeout(function () { btn.textContent = old; }, 1800);
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done(true); }).catch(function () { done(fallbackCopy(text)); });
      } else {
        done(fallbackCopy(text));
      }
    });
  });

  /* ---------------- Confirm destructive actions ---------------- */
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.getAttribute("data-confirm"))) e.preventDefault();
    });
  });

  /* ---------------- Dropdown menus ---------------- */
  var menus = Array.prototype.slice.call(document.querySelectorAll("[data-menu]"));
  function closeMenus(except) {
    menus.forEach(function (menu) {
      if (menu === except) return;
      menu.classList.remove("is-open");
      var toggle = menu.querySelector("[data-menu-toggle]");
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    });
  }
  menus.forEach(function (menu) {
    var toggle = menu.querySelector("[data-menu-toggle]");
    if (!toggle) return;
    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var open = menu.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
      closeMenus(menu);
    });
  });
  document.addEventListener("click", function () { closeMenus(null); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeMenus(null);
  });

  /* ---------------- QR modal ---------------- */
  var qrModal = document.getElementById("qrModal");
  var qrImage = document.getElementById("qrImage");
  var qrDownload = document.getElementById("qrDownload");
  var qrTitle = document.getElementById("qrTitle");

  document.querySelectorAll("[data-qr-url]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      if (!qrModal || !qrImage) return;
      var url = btn.getAttribute("data-qr-url");
      qrImage.src = url;
      if (qrDownload) {
        qrDownload.href = url;
        var slug = btn.getAttribute("data-qr") || "love-letter";
        qrDownload.setAttribute("download", "love-letter-" + slug + ".png");
      }
      if (qrTitle && btn.getAttribute("data-qr-title")) {
        qrTitle.textContent = btn.getAttribute("data-qr-title");
      }
      if (typeof qrModal.showModal === "function") qrModal.showModal();
      else window.open(url, "_blank", "noopener");
    });
  });

  document.querySelectorAll("[data-modal-close]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var dialog = btn.closest("dialog");
      if (dialog) dialog.close();
    });
  });

  document.querySelectorAll("dialog").forEach(function (dialog) {
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog) dialog.close();
    });
  });

  /* ---------------- Hero floating hearts ---------------- */
  var canvas = document.getElementById("heroHearts");
  if (canvas && !reduceMotion) {
    var ctx = canvas.getContext("2d");
    var hearts = [];
    var width = 0;
    var height = 0;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var colors = ["rgba(228,107,143,", "rgba(185,167,232,", "rgba(198,154,91,"];

    function sizeCanvas() {
      var rect = canvas.getBoundingClientRect();
      width = rect.width;
      height = rect.height;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function makeHeart(randomY) {
      return {
        x: Math.random() * width,
        y: randomY ? Math.random() * height : height + 30,
        size: 5 + Math.random() * 11,
        speed: 0.18 + Math.random() * 0.45,
        drift: (Math.random() - 0.5) * 0.35,
        phase: Math.random() * Math.PI * 2,
        wobble: 0.4 + Math.random() * 0.8,
        color: colors[Math.floor(Math.random() * colors.length)],
        alpha: 0.12 + Math.random() * 0.3,
        rotate: (Math.random() - 0.5) * 0.5
      };
    }

    function drawHeart(h) {
      var s = h.size;
      ctx.save();
      ctx.translate(h.x, h.y);
      ctx.rotate(h.rotate + Math.sin(h.phase) * 0.18);
      ctx.scale(s / 16, s / 16);
      ctx.beginPath();
      ctx.moveTo(0, 5);
      ctx.bezierCurveTo(-14, -6, -8, -16, 0, -8);
      ctx.bezierCurveTo(8, -16, 14, -6, 0, 5);
      ctx.closePath();
      ctx.fillStyle = h.color + h.alpha + ")";
      ctx.fill();
      ctx.restore();
    }

    function resize() {
      sizeCanvas();
      var count = Math.min(34, Math.max(12, Math.round(width / 42)));
      hearts = [];
      for (var i = 0; i < count; i++) hearts.push(makeHeart(true));
    }

    function frame() {
      ctx.clearRect(0, 0, width, height);
      hearts.forEach(function (h) {
        h.y -= h.speed;
        h.x += h.drift + Math.sin(h.phase) * 0.18;
        h.phase += 0.012 * h.wobble;
        if (h.y < -30) {
          var fresh = makeHeart(false);
          h.x = fresh.x; h.y = fresh.y; h.size = fresh.size;
          h.speed = fresh.speed; h.alpha = fresh.alpha; h.color = fresh.color;
        }
        drawHeart(h);
      });
      requestAnimationFrame(frame);
    }

    sizeCanvas();
    resize();
    window.addEventListener("resize", resize);
    frame();
  }

  /* ---------------- Footer year (optional hooks) ---------------- */
  document.documentElement.classList.add("js-ready");
})();
