/* =========================================================================
   TO MY LOVE — the recipient experience: envelope, typing, music, gallery
   ========================================================================= */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var body = document.body;
  var hasGsap = typeof window.gsap !== "undefined";
  var animation = body.getAttribute("data-animation") || "hearts";
  var opened = false;

  /* =====================================================================
     Ambient particles
     ===================================================================== */
  var particleHost = document.getElementById("particles");
  function initParticles() {
    if (!particleHost || animation === "none" || reduceMotion) return;
    var isMobile = window.innerWidth < 700;
    var count = isMobile ? 14 : 24;
    if (animation === "stars") count = isMobile ? 40 : 80;
    if (animation === "sparkles") count = isMobile ? 16 : 28;

    for (var i = 0; i < count; i++) {
      var el = document.createElement("span");
      el.className = "particle";
      var size = 10 + Math.random() * 14;
      var duration = 13 + Math.random() * 17;

      if (animation === "hearts") {
        el.classList.add("particle--heart");
        el.textContent = Math.random() > 0.75 ? "♡" : "♥";
        size = 9 + Math.random() * 18;
      } else if (animation === "petals") {
        el.classList.add("particle--petal");
        size = 8 + Math.random() * 13;
      } else if (animation === "sparkles") {
        el.classList.add("particle--sparkle");
        el.textContent = Math.random() > 0.5 ? "✦" : "✧";
        size = 7 + Math.random() * 11;
      } else {
        el.classList.add("particle--star");
        size = 1 + Math.random() * 2.6;
        duration = 8 + Math.random() * 14;
      }

      el.style.setProperty("--x", (Math.random() * 100).toFixed(2) + "%");
      el.style.setProperty("--size", size.toFixed(1) + "px");
      el.style.setProperty("--dur", duration.toFixed(1) + "s");
      el.style.setProperty("--delay", (-Math.random() * duration).toFixed(1) + "s");
      el.style.setProperty("--drift", ((Math.random() - 0.5) * 180).toFixed(0) + "px");
      el.style.setProperty("--rot", (Math.random() * 360).toFixed(0) + "deg");
      el.style.setProperty("--opacity", (0.25 + Math.random() * 0.5).toFixed(2));
      particleHost.appendChild(el);
    }
  }
  initParticles();

  /* =====================================================================
     Music
     ===================================================================== */
  var audio = document.getElementById("letterAudio");
  var musicButton = document.getElementById("musicToggle");
  var musicDock = document.querySelector("[data-music-dock]");
  var progressRing = document.getElementById("musicProgress");
  var circumference = 2 * Math.PI * 20;

  if (audio) audio.volume = 0.55;

  function updateMusicUI(playing) {
    if (musicButton) {
      musicButton.classList.toggle("is-playing", playing);
      musicButton.setAttribute("aria-pressed", String(playing));
      musicButton.setAttribute("aria-label", playing ? "Pause background music" : "Play background music");
    }
    if (musicDock) musicDock.classList.toggle("is-playing", playing);
  }

  function playMusic() {
    if (!audio) return;
    var promise = audio.play();
    if (promise && promise.then) {
      promise.then(function () { updateMusicUI(true); }).catch(function () { updateMusicUI(false); });
    } else {
      updateMusicUI(true);
    }
  }

  function toggleMusic() {
    if (!audio) return;
    if (audio.paused) playMusic();
    else {
      audio.pause();
      updateMusicUI(false);
    }
  }

  if (audio) {
    audio.addEventListener("play", function () { updateMusicUI(true); });
    audio.addEventListener("pause", function () { updateMusicUI(false); });
    audio.addEventListener("timeupdate", function () {
      if (!progressRing || !audio.duration) return;
      var progress = Math.min(1, audio.currentTime / audio.duration);
      progressRing.style.strokeDasharray = circumference;
      progressRing.style.strokeDashoffset = String(circumference * (1 - progress));
    });
    if (musicButton) musicButton.addEventListener("click", toggleMusic);
    document.querySelectorAll("[data-music-inline]").forEach(function (btn) {
      btn.addEventListener("click", toggleMusic);
    });
  }

  /* =====================================================================
     Envelope opening
     ===================================================================== */
  var openingScene = document.getElementById("openingScene");
  var letterScene = document.getElementById("letterScene");
  var envelope = document.getElementById("envelope");
  var openBtn = document.getElementById("openLetter");
  var hint = document.getElementById("envelopeHint");

  function burstHearts(sourceEl) {
    if (!sourceEl || reduceMotion) return;
    var rect = sourceEl.getBoundingClientRect();
    var cx = rect.left + rect.width / 2;
    var cy = rect.top + rect.height / 2;
    for (var i = 0; i < 16; i++) {
      var el = document.createElement("span");
      el.className = "burst-heart";
      el.textContent = Math.random() > 0.35 ? "♥" : "✦";
      el.style.left = cx + "px";
      el.style.top = cy + "px";
      el.style.fontSize = (9 + Math.random() * 20).toFixed(0) + "px";
      el.style.color = i % 3 === 0 ? "#c69a5b" : "";
      document.body.appendChild(el);
      var angle = (Math.PI * 2 * i) / 16 + Math.random() * 0.5;
      var dist = 90 + Math.random() * 220;
      var dx = Math.cos(angle) * dist;
      var dy = Math.sin(angle) * dist - 60;
      if (el.animate) {
        el.animate(
          [
            { transform: "translate(-50%, -50%) scale(0.4) rotate(0deg)", opacity: 1 },
            { transform: "translate(calc(-50% + " + dx + "px), calc(-50% + " + dy + "px)) scale(1) rotate(" + (Math.random() * 180 - 90) + "deg)", opacity: 0 }
          ],
          { duration: 1100 + Math.random() * 900, easing: "cubic-bezier(.2,.7,.3,1)", fill: "forwards" }
        ).onfinish = function () { el.remove(); };
      } else {
        setTimeout(function () { el.remove(); }, 1500);
      }
    }
  }

  function revealScene() {
    if (openingScene) openingScene.hidden = true;
    if (letterScene) letterScene.hidden = false;
    window.scrollTo(0, 0);

    var messageWrap = document.querySelector("[data-letter-message]");
    if (messageWrap && !reduceMotion) {
      messageWrap.querySelectorAll("p").forEach(function (p) {
        p.style.opacity = "0";
      });
    }

    var hero = document.querySelectorAll(".letter-hero > *");
    var paper = document.querySelector(".letter-paper");
    var countdown = document.querySelector(".countdown-card");
    var gallery = document.querySelector(".gallery-section");
    var closing = document.querySelector(".closing-section");

    if (hasGsap && !reduceMotion) {
      if (hero.length) gsap.from(hero, { y: 26, opacity: 0, duration: 0.9, stagger: 0.08, ease: "power3.out" });
      if (countdown) gsap.from(countdown, { y: 26, opacity: 0, duration: 0.8, delay: 0.25, ease: "power3.out" });
      if (paper) gsap.from(paper, { y: 60, opacity: 0, duration: 1.1, delay: 0.18, ease: "power3.out" });
      if (gallery && window.ScrollTrigger) {
        gsap.from(gallery.querySelectorAll(".polaroid"), {
          y: 50, opacity: 0, duration: 0.8, stagger: 0.1, ease: "power3.out",
          scrollTrigger: { trigger: gallery, start: "top 82%" }
        });
      }
      if (closing && window.ScrollTrigger) {
        gsap.from(closing.children, {
          y: 24, opacity: 0, duration: 0.9, stagger: 0.07, ease: "power3.out",
          scrollTrigger: { trigger: closing, start: "top 80%" }
        });
      }
      if (window.ScrollTrigger) setTimeout(function () { ScrollTrigger.refresh(); }, 700);
    }

    setTimeout(startTypewriter, 650);
  }

  function openLetter() {
    if (opened) return;
    opened = true;
    playMusic();
    if (hint) hint.style.opacity = "0";
    burstHearts(envelope);

    var flap = document.querySelector(".env-flap");
    var seal = document.querySelector(".env-seal");
    var letter = document.querySelector(".env-letter");
    var fadeTargets = document.querySelectorAll(
      ".opening-eyebrow, .opening-title, .opening-sub, #openLetter, .opening-note, .opening-bottom"
    );

    if (!hasGsap || reduceMotion) {
      revealScene();
      return;
    }

    gsap.set(envelope, { transformPerspective: 1100 });
    var tl = gsap.timeline({ defaults: { ease: "power2.inOut" } });
    tl.to(seal, { scale: 0.3, opacity: 0, duration: 0.4, ease: "back.in(2)" })
      .to(flap, { rotateX: -178, duration: 0.9, ease: "power2.inOut" }, 0.18)
      .to(letter, { opacity: 1, duration: 0.4, ease: "power1.out" }, 0.62)
      .to(letter, { y: "-38%", duration: 1.05, ease: "power3.out" }, 0.8)
      .to(".envelope-stage", { scale: 1.04, duration: 0.7 }, 0.8)
      .to(fadeTargets, { y: -16, opacity: 0, duration: 0.55, stagger: 0.04 }, 1.15)
      .to(".envelope-stage", { y: -46, scale: 1.12, opacity: 0, duration: 0.7, ease: "power2.in" }, 1.45)
      .add(function () { revealScene(); }, 1.85);
  }

  if (openBtn) openBtn.addEventListener("click", openLetter);
  if (envelope) {
    envelope.addEventListener("click", openLetter);
    envelope.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openLetter();
      }
    });
  }

  /* =====================================================================
     Typewriter
     ===================================================================== */
  var typingCancelled = false;
  var typingDone = false;

  function sleep(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  async function typeText(el, text, speed) {
    el.textContent = "";
    el.classList.add("is-typing");
    for (var i = 0; i < text.length; i++) {
      if (typingCancelled) break;
      el.textContent += text.charAt(i);
      if (i % 2 === 0) await sleep(speed);
    }
    if (typingCancelled) el.textContent = text;
    el.classList.remove("is-typing");
  }

  function finishTyping(paragraphs, titleEl, titleText, skipBtn) {
    typingCancelled = true;
    if (titleEl) {
      titleEl.textContent = titleText;
      titleEl.classList.add("is-typed");
    }
    paragraphs.forEach(function (p) {
      p.style.opacity = "";
      p.style.transform = "";
      if (p.dataset.originalText) p.textContent = p.dataset.originalText;
    });
    if (skipBtn) skipBtn.hidden = true;
    typingDone = true;
  }

  async function startTypewriter() {
    if (typingDone) return;
    var titleEl = document.querySelector("[data-typewriter]");
    var messageWrap = document.querySelector("[data-letter-message]");
    var skipBtn = document.getElementById("skipTyping");
    if (!messageWrap) return;

    var paragraphs = Array.prototype.slice.call(messageWrap.querySelectorAll("p"));
    var titleText = titleEl ? titleEl.textContent.trim() : "";
    paragraphs.forEach(function (p) { p.dataset.originalText = p.textContent; });

    if (reduceMotion) {
      if (titleEl) titleEl.classList.add("is-typed");
      return;
    }

    if (skipBtn) {
      skipBtn.hidden = false;
      skipBtn.addEventListener("click", function () {
        finishTyping(paragraphs, titleEl, titleText, skipBtn);
      }, { once: true });
    }

    if (titleEl && titleText) {
      titleEl.textContent = "";
      for (var i = 0; i < titleText.length; i++) {
        if (typingCancelled) break;
        titleEl.textContent += titleText.charAt(i);
        await sleep(32);
      }
      if (typingCancelled) titleEl.textContent = titleText;
      titleEl.classList.add("is-typed");
    }

    if (!paragraphs.length) return;
    paragraphs.forEach(function (p, index) {
      if (index === 0) {
        p.style.opacity = "1";
      } else {
        p.style.opacity = "0";
        p.style.transform = "translateY(10px)";
      }
    });

    await sleep(180);
    var first = paragraphs[0];
    var firstText = first.textContent;
    var speed = firstText.length > 300 ? 5 : firstText.length > 160 ? 10 : 16;
    await typeText(first, firstText, speed);
    if (typingCancelled) return;

    for (var j = 1; j < paragraphs.length; j++) {
      var p = paragraphs[j];
      p.style.transition = "opacity .7s ease, transform .7s ease";
      p.style.opacity = "1";
      p.style.transform = "none";
      await sleep(220);
    }
    if (skipBtn) skipBtn.hidden = true;
    typingDone = true;
  }

  /* =====================================================================
     Countdown
     ===================================================================== */
  var countdown = document.querySelector("[data-countdown]");
  if (countdown) {
    var targetDate = new Date(countdown.getAttribute("data-countdown") + "T00:00:00");
    var occasion = countdown.getAttribute("data-occasion") || "your special day";
    var label = countdown.querySelector("[data-countdown-label]");
    var cells = {
      days: countdown.querySelector("[data-cd-days]"),
      hours: countdown.querySelector("[data-cd-hours]"),
      mins: countdown.querySelector("[data-cd-mins]"),
      secs: countdown.querySelector("[data-cd-secs]")
    };

    var tick = function () {
      var now = new Date();
      var diff = targetDate.getTime() - now.getTime();
      if (isNaN(targetDate.getTime())) return;

      if (diff <= 0) {
        var daysSince = Math.floor(Math.abs(diff) / 86400000);
        countdown.classList.add("is-past");
        if (Math.abs(diff) < 86400000) {
          if (label) label.textContent = "Today is the day ✦";
        } else if (label) {
          label.textContent = daysSince.toLocaleString() + " day" + (daysSince === 1 ? "" : "s") + " since " + occasion.toLowerCase() + " — and still counting";
        }
        return;
      }

      var totalSeconds = Math.floor(diff / 1000);
      var days = Math.floor(totalSeconds / 86400);
      var hours = Math.floor((totalSeconds % 86400) / 3600);
      var minutes = Math.floor((totalSeconds % 3600) / 60);
      var seconds = totalSeconds % 60;
      var pad = function (n) { return n < 10 ? "0" + n : String(n); };
      if (cells.days) cells.days.textContent = pad(days);
      if (cells.hours) cells.hours.textContent = pad(hours);
      if (cells.mins) cells.mins.textContent = pad(minutes);
      if (cells.secs) cells.secs.textContent = pad(seconds);
      if (label) label.textContent = "Counting down to " + occasion.toLowerCase();
    };
    tick();
    setInterval(tick, 1000);
  }

  /* =====================================================================
     Gallery lightbox
     ===================================================================== */
  var lightbox = document.getElementById("lightbox");
  var lightboxImage = document.getElementById("lightboxImage");
  var lightboxCaption = document.getElementById("lightboxCaption");
  var lightboxCount = document.getElementById("lightboxCount");
  var photoButtons = Array.prototype.slice.call(document.querySelectorAll("[data-lightbox-index]"));
  var photoIndex = 0;

  function showPhoto(index) {
    if (!photoButtons.length || !lightboxImage) return;
    photoIndex = (index + photoButtons.length) % photoButtons.length;
    var btn = photoButtons[photoIndex];
    var src = btn.getAttribute("data-src");
    var caption = btn.getAttribute("data-caption");
    lightboxImage.src = src;
    lightboxImage.alt = caption || "A shared memory";
    if (lightboxCaption) {
      lightboxCaption.textContent = caption || "";
      lightboxCaption.hidden = !caption;
    }
    if (lightboxCount) lightboxCount.textContent = (photoIndex + 1) + " / " + photoButtons.length;
  }

  function openLightbox(index) {
    if (!lightbox) return;
    showPhoto(index);
    if (typeof lightbox.showModal === "function") lightbox.showModal();
    else window.open(photoButtons[index].getAttribute("data-src"), "_blank", "noopener");
  }

  photoButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      openLightbox(parseInt(btn.getAttribute("data-lightbox-index"), 10));
    });
  });

  if (lightbox) {
    var closeBtn = lightbox.querySelector("[data-lightbox-close]");
    var prevBtn = lightbox.querySelector("[data-lightbox-prev]");
    var nextBtn = lightbox.querySelector("[data-lightbox-next]");
    if (closeBtn) closeBtn.addEventListener("click", function () { lightbox.close(); });
    if (prevBtn) prevBtn.addEventListener("click", function () { showPhoto(photoIndex - 1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { showPhoto(photoIndex + 1); });
    lightbox.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") showPhoto(photoIndex - 1);
      if (e.key === "ArrowRight") showPhoto(photoIndex + 1);
    });
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) lightbox.close();
    });
  }

  /* =====================================================================
     Small niceties
     ===================================================================== */
  // Pause music when the tab is hidden and resume if it was playing.
  var wasPlaying = false;
  document.addEventListener("visibilitychange", function () {
    if (!audio) return;
    if (document.hidden) {
      wasPlaying = !audio.paused;
      if (wasPlaying) audio.pause();
    } else if (wasPlaying) {
      audio.play().catch(function () {});
    }
  });

  // Keep the lightbox image from being dragged around.
  if (lightboxImage) lightboxImage.addEventListener("dragstart", function (e) { e.preventDefault(); });
})();
