;if ("serviceWorker" in navigator) {
  console.log("Service Worker is supported");
  window.addEventListener("load", function () {
    navigator.serviceWorker.register("/static/javascript/sw.js")
      .then(function (registration) {
        console.log("Service Worker registered with scope:", registration.scope);
      })
      .catch(function (error) {
        console.error("Service Worker registration failed:", error);
      });
  });
}
