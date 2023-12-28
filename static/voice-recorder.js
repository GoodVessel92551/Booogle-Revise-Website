const record = (id, voice_id) => {
  if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
    const recognition = new (window.SpeechRecognition ||
      window.webkitSpeechRecognition)();
    if (!recognition) {
      console.log("Speech recognition is not available");
    } else if (!("ontouchstart" in window)) {
      document.getElementById(voice_id).style.color = "#af8888";
      const recognition = new (window.SpeechRecognition ||
        window.webkitSpeechRecognition)();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      let lastResult = "";
      recognition.onresult = () => {
        lastResult = event.results[0][0].transcript;
        lastResult = lastResult
          .replace(" full stop", ".")
          .replace(" question mark", "?")
          .replace(" exclamation mark", "!")
          .replace("full stop", ".")
          .replace("question mark", "?")
          .replace("exclamation mark", "!");
        lastResult = lastResult.split(/(?<=\.|\?|\!)\s/);
        lastResult = lastResult.map(
          (lastResult) =>
            lastResult.charAt(0).toUpperCase() + lastResult.slice(1)
        );
        lastResult = lastResult.join(" ");
        document.getElementById(id).value =
          document.getElementById(id).value + lastResult;
      };
      recognition.onend = () => {
        document.getElementById(voice_id).style.color = "#fff";
      };
      recognition.start();
    }
  }
};
