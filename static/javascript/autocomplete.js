var spelling_words = [];
var possible_answer = "";
fetch("/static/resources/text.txt")
  .then((response) => response.text())
  .then((data) => {
    var words = data.toLowerCase().match(/\b\w+\b/g);
    var word_freq = {};
    for (var i = 0; i < words.length; i++) {
      if (word_freq[words[i]]) {
        word_freq[words[i]]++;
      } else {
        word_freq[words[i]] = 1;
      }
    }
    var sortedWords = Object.keys(word_freq).sort(function (a, b) {
      return word_freq[b] - word_freq[a];
    });
    autocomplete(sortedWords);
  })
  .catch((error) => console.error(error));

fetch("/static/resources/words.txt")
   
  .then((response) => response.text())
  .then((data) => {
    var words = data.toLowerCase().match(/\b\w+\b/g);
    spelling_words = words;
  })
  .catch((error) => console.error(error));
    

const levenshteinDistance = (a, b) => {
  const distanceMatrix = Array(b.length + 1)
    .fill(null)
    .map(() => Array(a.length + 1).fill(null));

  for (let i = 0; i <= a.length; i++) {
    distanceMatrix[0][i] = i;
  }

  for (let j = 0; j <= b.length; j++) {
    distanceMatrix[j][0] = j;
  }

  for (let j = 1; j <= b.length; j++) {
    for (let i = 1; i <= a.length; i++) {
      const substitutionCost = a[i - 1] === b[j - 1] ? 0 : 1;
      distanceMatrix[j][i] = Math.min(
        distanceMatrix[j][i - 1] + 1,
        distanceMatrix[j - 1][i] + 1,
        distanceMatrix[j - 1][i - 1] + substitutionCost
      );
    }
  }

  return distanceMatrix[b.length][a.length];
};

const spellCheck = (word) => {
  var dictionary = spelling_words;
  const maxDistance = 2;
  var bestMatch = null;
  var bestDistance = Infinity;

  for (let i = 0; i < dictionary.length; i++) {
    const distance = levenshteinDistance(word, dictionary[i]);
    if (distance < bestDistance && distance <= maxDistance) {
      bestMatch = dictionary[i];
      bestDistance = distance;
    }
  }
  return {
    word: bestMatch,
    confidence: 1 - bestDistance / Math.max(word.length, bestMatch.length),
  };
};

const autocomplete = (sortedWords) => {
  const complete = (input, current, next, button,possible_answer) => {
    console.log(possible_answer)
    var word_list = input.value.split(" ");
    var current_word = word_list[word_list.length - 1].toLowerCase();
    if (word_list.length > 1 && spell) {
      var word_before = word_list[word_list.length - 2];
     var spell = spellCheck(word_before.toLowerCase());
      if (spell["confidence"] > 0.6) {
        if (spell["confidence"] != 1) {
          input.value = input.value.replace(word_before, spell["word"]);
            current.value = input.value.replace(word_before, spell["word"]);
        }
      }
      console.log(spellCheck(word_before));
    }
    var done = false;
    current.innerText = input.value;
    next.innerHTML = "";
    button.style.display = "none";
    if (input.value != "") {
      for (var i = 0; i < sortedWords.length; i++) {
        if (sortedWords[i].startsWith(current_word.toLowerCase())) {
          if (
            sortedWords[i].toLowerCase() != current_word.toLowerCase() &&
            current_word.length >= 1
          ) {
            button.style.display = "inline-block";
            var remanding = sortedWords[i].slice(current_word.length);
            next.innerText = remanding;
            input.addEventListener("keydown", (e) => {
              if (e.which === 9 && !done) {
                e.preventDefault();
                input.value += next.innerText;
                done = true;
                next.innerHTML = "";
                button.style.display = "none";
              }
            });
            button.addEventListener("click", (e) => {
              input.focus();
              input.value += next.innerText;
              next.innerHTML = "";
              button.style.display = "none";
            });
            break;
          }
        }
      }
    }else if (possible_answer != ""){
      input.placeholder = "";
      next.innerText = possible_answer;
      input.addEventListener("keydown", (e) => {
        if (e.which === 9 && !done) {
          e.preventDefault();
          input.value += next.innerText;
          done = true;
          next.innerHTML = "";
          button.style.display = "none";
        }
      });
      button.addEventListener("click", (e) => {
        input.focus();
        input.value += next.innerText;
        next.innerHTML = "";
        button.style.display = "none";
      });
    }
  };
  var input = document.getElementById("quest");
  var current = document.getElementById("quest_autocomplete_current");
  var next = document.getElementById("quest_autocomplete_next");
  var button = document.getElementById("quest_autocomplete_button");
  input.addEventListener("input", () => {
    var spell = input.value[input.value.length - 1] === " ";
    spell = false
    console.log(input.value)
    if (input.value.includes("?")){
      console.log("yes")
      data = {
        "question": input.value
      }
      fetch("/api/ai/answer",{
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      })
      .then((response) => response.json())
      .then ((data) => {
        possible_answer = data["answer"];
        console.log(data)
      })
    }
    complete(input, current, next, button,spell,"");
  });
  input.addEventListener("blur", () => {
    next.innerHTML = "";
    button.style.display = "none";
  });
  var ans_input = document.getElementById("ans1");
  var ans_current = document.getElementById("ans_autocomplete_current");
  var ans_next = document.getElementById("ans_autocomplete_next");
  var ans_button = document.getElementById("ans_autocomplete_button");
  ans_input.addEventListener("input", () => {
    complete(ans_input, ans_current, ans_next, ans_button,possible_answer);
  });
  ans_input.addEventListener("blur", () => {
    ans_next.innerHTML = "";
    ans_button.style.display = "none";
    ans_input.placeholder = "Description";
  });

  ans_input.addEventListener("click", () => {
    complete(ans_input, ans_current, ans_next, ans_button,possible_answer);
  });
};




