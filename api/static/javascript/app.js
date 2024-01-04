if ("windowControlsOverlay" in navigator) {
  document.getElementById("top_text").style.display = "none";
}

if ("serviceWorker" in navigator) {
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/sw.js");
  });
}

if (navigator.windowControlsOverlay.visible) {
  document.getElementById("top_text").style.display = "flex";
}
