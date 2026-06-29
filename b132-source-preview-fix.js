(function () {
  function previewFrame() {
    return document.querySelector('iframe[name="sourcePreview"], iframe#sourcePreview, iframe#frame');
  }

  function sourceNote() {
    return document.querySelector(".source-note") || document.querySelector("[data-source-preview-note]");
  }

  function visibleEnough(el) {
    if (!el) return false;
    var rect = el.getBoundingClientRect();
    return rect.width > 120 && rect.height > 120 && rect.bottom > 80 && rect.top < window.innerHeight - 80;
  }

  function scrollPreviewIntoView(frame) {
    if (!frame) return;
    var compact = window.matchMedia("(max-width: 760px)").matches;
    frame.scrollIntoView({
      behavior: "smooth",
      block: compact || !visibleEnough(frame) ? "start" : "nearest"
    });
    frame.classList.add("b132-preview-just-opened");
    window.setTimeout(function () {
      frame.classList.remove("b132-preview-just-opened");
    }, 1400);
  }

  function installStyle() {
    if (document.getElementById("b132-source-preview-fix-style")) return;
    var style = document.createElement("style");
    style.id = "b132-source-preview-fix-style";
    style.textContent = [
      "iframe[name='sourcePreview'], iframe#sourcePreview, iframe#frame{",
      "  min-height:min(78vh,720px);",
      "}",
      "iframe[name='sourcePreview'].b132-preview-just-opened, iframe#frame.b132-preview-just-opened{",
      "  outline:3px solid #0f766e; outline-offset:3px;",
      "  box-shadow:0 0 0 6px rgba(15,118,110,.12);",
      "}",
      "body.b132-preview-expanded iframe[name='sourcePreview'], body.b132-preview-expanded iframe#sourcePreview, body.b132-preview-expanded iframe#frame{",
      "  height:calc(100vh - 128px) !important;",
      "  min-height:760px !important;",
      "}",
      ".b132-preview-toolbar{",
      "  display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin:8px 0 10px;",
      "}",
      ".b132-preview-toolbar button{",
      "  border:1px solid #cbd5e1; border-radius:7px; padding:7px 10px; background:#f8fafc; color:#172033; font:inherit; font-size:13px; cursor:pointer;",
      "}",
      ".b132-preview-toolbar button:first-child{",
      "  background:#0f766e; color:white; border-color:#0f766e;",
      "}",
      ".b132-preview-toolbar span{",
      "  font-size:13px; color:#64748b;",
      "}",
      ".b132-preview-active-link{",
      "  background:#dcfce7 !important; color:#14532d !important; border-color:#22c55e !important;",
      "}",
      "@media(max-width:700px){iframe[name='sourcePreview'], iframe#sourcePreview, iframe#frame{min-height:520px;} body.b132-preview-expanded iframe[name='sourcePreview'], body.b132-preview-expanded iframe#sourcePreview, body.b132-preview-expanded iframe#frame{min-height:560px !important;}}"
    ].join("");
    document.head.appendChild(style);
  }

  function readableName(src) {
    if (!src) return "未載入";
    try {
      var url = new URL(src, window.location.href);
      return decodeURIComponent(url.pathname.split("/").pop() || url.href);
    } catch (e) {
      return src;
    }
  }

  function installToolbar(frame) {
    if (!frame) return;
    if (document.getElementById("toggleLargePreview") || document.querySelector(".b132-preview-toolbar")) return;
    var toolbar = document.createElement("div");
    toolbar.className = "b132-preview-toolbar";

    var expand = document.createElement("button");
    expand.type = "button";
    expand.textContent = "放大切頁區";

    var open = document.createElement("button");
    open.type = "button";
    open.textContent = "另開目前切頁";

    var label = document.createElement("span");

    function currentSrc() {
      return frame.getAttribute("src") || frame.src || "";
    }
    function refreshLabel() {
      label.textContent = "目前：" + readableName(currentSrc());
    }

    expand.addEventListener("click", function () {
      document.body.classList.toggle("b132-preview-expanded");
      expand.textContent = document.body.classList.contains("b132-preview-expanded") ? "恢復預覽大小" : "放大切頁區";
      window.setTimeout(refreshLabel, 80);
    });
    open.addEventListener("click", function () {
      var src = currentSrc();
      if (src) window.open(src, "_blank", "noopener");
    });
    frame.addEventListener("load", refreshLabel);
    toolbar.appendChild(expand);
    toolbar.appendChild(open);
    toolbar.appendChild(label);
    frame.parentNode.insertBefore(toolbar, frame);
    refreshLabel();
  }

  function markActive(anchor) {
    document.querySelectorAll("a.b132-preview-active-link").forEach(function (link) {
      link.classList.remove("b132-preview-active-link");
    });
    anchor.classList.add("b132-preview-active-link");
  }

  function updateNote(anchor) {
    var note = sourceNote();
    if (!note) return;
    var label = anchor.textContent.trim() || "原書切頁";
    note.textContent = "已開啟：" + label + "。如果你沒有看到 PDF，頁面會自動移到預覽框；完整 PDF 連結仍可另開。";
  }

  document.addEventListener("click", function (event) {
    var anchor = event.target.closest && event.target.closest('a[target="sourcePreview"]');
    if (!anchor) return;
    var frame = previewFrame();
    if (!frame) {
      anchor.removeAttribute("target");
      return;
    }
    event.preventDefault();
    frame.setAttribute("src", anchor.getAttribute("href"));
    markActive(anchor);
    updateNote(anchor);
    window.setTimeout(function () {
      scrollPreviewIntoView(frame);
    }, 120);
  }, true);

  window.addEventListener("load", function () {
    installStyle();
    var frame = previewFrame();
    if (frame) {
      frame.setAttribute("tabindex", "0");
      installToolbar(frame);
    }
  });
})();
