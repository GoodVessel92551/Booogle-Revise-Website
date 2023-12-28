const voice = (text) => {
  if ("speechSynthesis" in window) {
    var utterance = new SpeechSynthesisUtterance();
    utterance.text = text;
    speechSynthesis.speak(utterance);
  } else {
    console.log("Unavailable");
  }
};
