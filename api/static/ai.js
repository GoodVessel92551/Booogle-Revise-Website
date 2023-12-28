var prompt = document.getElementById("prompt");
var button = document.getElementById("button");

const gen = (() => {
    console.log("Generating");
})

prompt.addEventListener("keyup",(e) => {
    if(e.key == "Enter" && prompt.value != "" && !generating){
        gen();
    }
})