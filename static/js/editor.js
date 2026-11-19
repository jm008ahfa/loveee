/* =========================================================================
   TO MY LOVE — love letter creator
   ========================================================================= */
(function () {
  "use strict";

  var form = document.getElementById("letterForm");
  if (!form) return;

  var csrfInput = form.querySelector("[name=csrfmiddlewaretoken]");
  var csrfToken = csrfInput ? csrfInput.value : "";
  var steps = Array.prototype.slice.call(document.querySelectorAll("[data-step-btn]"));
  var panels = Array.prototype.slice.call(document.querySelectorAll("[data-step-panel]"));
  var current = 0;
  var dirty = false;
  var submitting = false;

  var FONTS = {
    elegant: "'Cormorant Garamond', serif",
    handwritten: "'Caveat', cursive",
    romantic: "'Great Vibes', cursive",
    classic: "'Libre Baskerville', Georgia, serif",
    modern: "'Outfit', sans-serif",
    typewriter: "'Courier Prime', monospace"
  };

  /* ---------------- Steps ---------------- */
  function showStep(index) {
    current = Math.max(0, Math.min(panels.length - 1, index));
    panels.forEach(function (panel, i) {
      var active = i === current;
      panel.hidden = !active;
      panel.classList.toggle("is-active", active);
    });
    steps.forEach(function (step, i) {
      step.classList.toggle("is-active", i === current);
    });
    var nav = document.querySelector(".editor-steps");
    if (nav) {
      var top = nav.getBoundingClientRect().top + window.scrollY - 90;
      window.scrollTo({ top: top, behavior: "smooth" });
    }
  }

  steps.forEach(function (step, i) {
    step.addEventListener("click", function () { showStep(i); });
  });
  document.querySelectorAll("[data-next-step]").forEach(function (btn) {
    btn.addEventListener("click", function () { showStep(current + 1); });
  });
  document.querySelectorAll("[data-prev-step]").forEach(function (btn) {
    btn.addEventListener("click", function () { showStep(current - 1); });
  });

  // If the server returned errors, open the step containing the first one.
  var firstError = form.querySelector(".field-error, .form-alert");
  if (firstError) {
    var panel = firstError.closest("[data-step-panel]");
    if (panel) showStep(panels.indexOf(panel));
  }

  /* ---------------- Live preview ---------------- */
  var mini = document.querySelector("[data-mini-letter]");
  var miniFor = document.querySelector("[data-mini-for]");
  var miniTitle = document.querySelector("[data-mini-title]");
  var miniMessage = document.querySelector("[data-mini-message]");
  var miniSender = document.querySelector("[data-mini-sender]");
  var miniDate = document.querySelector("[data-mini-date]");
  var miniMusic = document.querySelector("[data-mini-music]");
  var miniFont = document.querySelector("[data-mini-font]");
  var miniAnimation = document.querySelector("[data-mini-animation]");

  function field(name) { return form.querySelector("[name='" + name + "']"); }

  function checkedValue(name) {
    var el = form.querySelector("input[name='" + name + "']:checked");
    return el ? el.value : "";
  }

  function refreshPreview() {
    var recipient = field("recipient_name");
    var sender = field("sender_name");
    var title = field("title");
    var message = field("message");
    var date = field("special_date");

    if (miniFor) miniFor.textContent = recipient && recipient.value.trim() ? "For " + recipient.value.trim() : "For the one you love";
    if (miniTitle) miniTitle.textContent = title && title.value.trim() ? title.value.trim() : "Your letter title";
    if (miniSender) miniSender.textContent = sender && sender.value.trim() ? sender.value.trim() : "You";
    if (miniMessage) {
      var text = message && message.value.trim() ? message.value.trim() : "Your words will appear here as you write them — soft, warm, and completely yours.";
      miniMessage.textContent = text.length > 230 ? text.slice(0, 230).trimEnd() + "…" : text;
    }
    if (miniDate) {
      if (date && date.value) {
        var d = new Date(date.value + "T12:00:00");
        if (!isNaN(d.getTime())) {
          miniDate.textContent = d.toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" });
        }
      } else {
        miniDate.textContent = new Date().toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" });
      }
    }
    if (miniFont) {
      var f = checkedValue("font_style");
      var labelEl = form.querySelector("input[name='font_style']:checked");
      var textLabel = "Handwritten";
      if (labelEl) {
        var option = labelEl.closest(".font-option");
        if (option) textLabel = option.querySelector(".font-option__name").textContent;
      }
      miniFont.textContent = textLabel;
      if (mini) mini.style.setProperty("--letter-font", FONTS[f] || FONTS.handwritten);
    }
    if (miniAnimation) {
      var a = checkedValue("animation");
      var animEl = form.querySelector("input[name='animation']:checked");
      miniAnimation.textContent = animEl ? animEl.closest(".choice-chip").textContent.trim() : "Hearts";
    }
  }

  function applyTheme(option) {
    if (!mini || !option) return;
    mini.style.setProperty("--m-primary", option.getAttribute("data-primary"));
    mini.style.setProperty("--m-secondary", option.getAttribute("data-secondary"));
    mini.style.setProperty("--m-accent", option.getAttribute("data-accent"));
    mini.style.setProperty("--m-paper", option.getAttribute("data-paper"));
    mini.style.setProperty("--m-ink", option.getAttribute("data-ink"));
    mini.style.setProperty("--m-bg", option.getAttribute("data-bg"));
    mini.style.setProperty("--heading-font", option.getAttribute("data-heading"));
    var title = document.querySelector("[data-mini-title]");
    if (title) title.style.color = option.getAttribute("data-accent");
  }

  form.querySelectorAll("input[name='theme']").forEach(function (radio) {
    radio.addEventListener("change", function () {
      applyTheme(radio.closest("[data-theme-option]"));
    });
  });
  var checkedTheme = form.querySelector("input[name='theme']:checked");
  if (!checkedTheme) {
    var firstTheme = form.querySelector("input[name='theme']");
    if (firstTheme) firstTheme.checked = true;
    checkedTheme = firstTheme;
  }
  if (checkedTheme) applyTheme(checkedTheme.closest("[data-theme-option]"));

  form.querySelectorAll("input[name='font_style'], input[name='animation'], input[name='occasion']").forEach(function (radio) {
    radio.addEventListener("change", refreshPreview);
  });

  ["recipient_name", "sender_name", "title", "message", "special_date", "closing_note"].forEach(function (name) {
    var el = field(name);
    if (el) el.addEventListener("input", refreshPreview);
  });

  var messageEl = field("message");
  var messageCount = document.querySelector("[data-message-count]");
  function updateCount() {
    if (!messageEl || !messageCount) return;
    var len = messageEl.value.length;
    messageCount.textContent = len.toLocaleString() + " character" + (len === 1 ? "" : "s");
    if (len > 8000) messageCount.classList.add("is-over");
    else messageCount.classList.remove("is-over");
  }
  if (messageEl) {
    messageEl.addEventListener("input", updateCount);
    updateCount();
  }
  refreshPreview();

  /* ---------------- Music ---------------- */
  var musicSelect = document.querySelector("[data-music-select]");
  var playBtn = document.querySelector("[data-music-play]");
  var stopBtn = document.querySelector("[data-music-stop]");
  var nowLabel = document.querySelector("[data-music-now]");
  var previewAudio = null;

  function stopPreview() {
    if (previewAudio) {
      previewAudio.pause();
      previewAudio.currentTime = 0;
      previewAudio = null;
    }
    if (stopBtn) stopBtn.hidden = true;
    if (playBtn) playBtn.textContent = "▶ Play a little";
  }

  function selectedTrack() {
    if (!musicSelect) return null;
    return musicSelect.options[musicSelect.selectedIndex] || null;
  }

  if (musicSelect) {
    musicSelect.addEventListener("change", function () {
      stopPreview();
      var opt = selectedTrack();
      if (nowLabel) nowLabel.textContent = opt && opt.value ? opt.getAttribute("data-title") || opt.text : "A quiet letter — no music.";
      if (miniMusic) miniMusic.textContent = opt && opt.value ? opt.getAttribute("data-title") || "our song" : "no music yet";
    });
    var opt0 = selectedTrack();
    if (miniMusic) miniMusic.textContent = opt0 && opt0.value ? opt0.getAttribute("data-title") || "our song" : "no music yet";
  }

  if (playBtn) {
    playBtn.addEventListener("click", function () {
      var opt = selectedTrack();
      var src = opt && opt.getAttribute("data-src");
      if (!src) {
        if (nowLabel) nowLabel.textContent = "Choose a track first — or upload your own below.";
        return;
      }
      if (previewAudio && !previewAudio.paused) {
        stopPreview();
        return;
      }
      stopPreview();
      previewAudio = new Audio(src);
      previewAudio.volume = 0.7;
      previewAudio.play().then(function () {
        playBtn.textContent = "❚❚ Pause";
        if (stopBtn) stopBtn.hidden = false;
        if (nowLabel) nowLabel.textContent = "Playing " + (opt.getAttribute("data-title") || "your song") + "…";
      }).catch(function () {
        if (nowLabel) nowLabel.textContent = "Your browser blocked playback. Try once more.";
      });
      previewAudio.addEventListener("ended", stopPreview);
    });
  }
  if (stopBtn) stopBtn.addEventListener("click", stopPreview);

  /* ---------------- Photos ---------------- */
  var input = document.querySelector("[data-photo-input]");
  var dropzone = document.querySelector("[data-dropzone]");
  var uploadPreview = document.querySelector("[data-upload-preview]");
  var maxPhotos = input ? parseInt(input.getAttribute("data-max"), 10) || 12 : 12;
  var existingCount = document.querySelectorAll("[data-photo-grid] .photo-card").length;

  function showSelectedFiles(files) {
    if (!uploadPreview) return;
    uploadPreview.innerHTML = "";
    Array.prototype.forEach.call(files, function (file) {
      if (!file.type || file.type.indexOf("image/") !== 0) return;
      var figure = document.createElement("figure");
      var img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.alt = "";
      var cap = document.createElement("figcaption");
      cap.textContent = file.name.length > 18 ? file.name.slice(0, 15) + "…" : file.name;
      figure.appendChild(img);
      figure.appendChild(cap);
      uploadPreview.appendChild(figure);
    });
    if (dropzone) {
      var title = dropzone.querySelector(".dropzone__title");
      if (title && files.length) {
        title.innerHTML = "<strong>" + files.length + "</strong> photo" + (files.length === 1 ? "" : "s") + " ready to upload";
      }
    }
    dirty = true;
  }

  if (input) {
    input.addEventListener("change", function () {
      var files = Array.prototype.slice.call(input.files);
      if (files.length + existingCount > maxPhotos) {
        window.alert("You can add up to " + maxPhotos + " photos per letter. Please choose fewer.");
        input.value = "";
        showSelectedFiles([]);
        if (dropzone) {
          var title = dropzone.querySelector(".dropzone__title");
          if (title) title.innerHTML = "Drop photos here, or <em>choose from your device</em>";
        }
        updatePhotoCount();
        return;
      }
      showSelectedFiles(files);
      updatePhotoCount(files.length);
    });
  }

  function updatePhotoCount(selected) {
    var counter = document.querySelector("[data-mini-photo-count]");
    if (counter) counter.textContent = String(existingCount + (selected || 0));
  }

  if (dropzone && input) {
    ["dragenter", "dragover"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.add("is-dragover");
      });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        dropzone.classList.remove("is-dragover");
      });
    });
    dropzone.addEventListener("drop", function (e) {
      var files = e.dataTransfer.files;
      if (!files || !files.length) return;
      if (files.length + existingCount > maxPhotos) {
        window.alert("You can add up to " + maxPhotos + " photos per letter.");
        return;
      }
      try {
        input.files = files;
      } catch (err) { /* older browsers */ }
      showSelectedFiles(files);
    });
  }

  /* Delete existing photo */
  document.querySelectorAll("[data-photo-delete]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (!window.confirm("Remove this photo from your letter?")) return;
      var card = btn.closest(".photo-card");
      fetch(btn.getAttribute("data-photo-delete"), {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin"
      }).then(function (res) {
        if (!res.ok) throw new Error("Could not remove photo");
        if (card) card.remove();
        existingCount = Math.max(0, existingCount - 1);
        updatePhotoCount();
        refreshPreview();
      }).catch(function () {
        window.alert("Sorry, that photo could not be removed. Please refresh and try again.");
      });
    });
  });

  /* Reorder existing photos */
  var photoGrid = document.querySelector("[data-photo-grid]");
  if (photoGrid) {
    var dragged = null;
    photoGrid.querySelectorAll(".photo-card").forEach(function (card) {
      card.addEventListener("dragstart", function (e) {
        dragged = card;
        card.classList.add("is-dragging");
        e.dataTransfer.effectAllowed = "move";
        try { e.dataTransfer.setData("text/plain", card.getAttribute("data-photo-id")); } catch (err) {}
      });
      card.addEventListener("dragend", function () {
        card.classList.remove("is-dragging");
        dragged = null;
      });
      card.addEventListener("dragover", function (e) {
        e.preventDefault();
        if (!dragged || dragged === card) return;
        var rect = card.getBoundingClientRect();
        var after = (e.clientX - rect.left) > rect.width / 2;
        photoGrid.insertBefore(dragged, after ? card.nextSibling : card);
      });
      card.addEventListener("drop", function (e) { e.preventDefault(); });
    });

    photoGrid.addEventListener("drop", function () {
      if (!photoGrid) return;
      var ids = Array.prototype.map.call(photoGrid.querySelectorAll(".photo-card"), function (card) {
        return parseInt(card.getAttribute("data-photo-id"), 10);
      });
      fetch(photoGrid.getAttribute("data-reorder-url") || window.location.pathname.replace(/\/edit\/?$/, "/photos/reorder/"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
          "X-Requested-With": "XMLHttpRequest"
        },
        credentials: "same-origin",
        body: JSON.stringify({ order: ids })
      }).catch(function () {});
    });
  }

  /* ---------------- Dirty state ---------------- */
  form.addEventListener("input", function () { dirty = true; });
  form.addEventListener("change", function () { dirty = true; });
  form.addEventListener("submit", function () { submitting = true; });
  window.addEventListener("beforeunload", function (e) {
    if (dirty && !submitting) {
      e.preventDefault();
      e.returnValue = "";
    }
  });

  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
      e.preventDefault();
      var draftBtn = form.querySelector("button[name='action'][value='draft']");
      if (draftBtn) {
        submitting = true;
        draftBtn.click();
      }
    }
  });
})();
