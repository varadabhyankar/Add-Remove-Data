const options = document.getElementById('options');
const textFieldContainer = document.getElementById('textFieldContainer');
const newSelectContainer = document.getElementById('newSelectContainer');
const submitButton = document.getElementById('submitButton');
const textFieldLabel = document.getElementById('textLabel');
const selectBox = document.getElementById('newSelect');
const newTextLabel = document.getElementById('newSelectLabel');
const textFieldBox = document.getElementById('textField');
const responseBox = document.getElementById("response_text");
const queryLabel = document.getElementById("textLabel");
const audioButton = document.getElementById("recordAudio");
let audio_recording = false;

const SpeechRecognition = window.SpeechRecongition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.interimResults = true;
recognition.continuous = true;
recognition.onresult = (event) => {
    let transcript = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
    }
    textFieldBox.value = transcript;
};
recognition.onerror = (event) => {
    console.error("Speech recognition error", event)
};
recognition.onend = () => {
    audio_recording = false;
    audioButton.textContent = 'Record';
};


// Use a regular expression to extract `<name>` from the URL
const currentUrl = window.location.href;
const nameMatch = currentUrl.match(/\/run_query\/([^/]+)/);

if (nameMatch && nameMatch[1]) {
    const name = nameMatch[1]; // Extracted <name>
    const form = document.getElementById('dynamicForm');
    console.log(name);
    form.action = `/get_llm_response/${name}`;
}


options.addEventListener('change', function () {
    const selectedOption = options.value;

    // Reset all fields and button visibility
    newSelectContainer.style.display = 'none';
    queryLabel.style.display = 'inline-block';
    textFieldContainer.style.display = 'flex';
    textFieldBox.required = true;
    audioButton.style = "background-color:grey; padding:0.5rem; flex-basis:content; margin-left:1rem;"
    audio_recording ? audioButton.innerText = "Stop" : audioButton.innerText = "Record";
    submitButton.style.display = 'inline-block';
    selectBox.innerHTML = '';

    if (['course_query', 'research_paper'].includes(selectedOption)) {
        newSelectContainer.style.display = 'block'; // Show new select
        if(selectedOption==="course_query"){
            newTextLabel.innerHTML = "Course you want talk about:";
            getFileList("course").then(file_list=> {
                for( let file_name of file_list){
                    let opt = document.createElement('option');
                    opt.value = file_name;
                    opt.innerText = file_name;
                    selectBox.appendChild(opt);
                }
            });
        }
        else if(selectedOption==="research_paper"){
            newTextLabel.innerHTML = "Paper you want to talk about:";
            getFileList("research").then(file_list=> {
                for( let file_name of file_list){
                    let opt = document.createElement('option');
                    opt.value = file_name;
                    opt.innerText = file_name;
                    selectBox.appendChild(opt);
                }
            });
        }
    }
});

document.getElementById('dynamicForm').addEventListener('submit', function (event) {
    // Example of handling the form submit and sending data via POST
    event.preventDefault(); // Prevent default form submission
    const formData = new FormData(this);
    fetch(this.action, {
        method: this.method,
        body: formData
    })
    .then(response => response.json())
    .then(response => JSON.stringify(response))
    .then(response => response.replaceAll('\\n',"<br>"))
    .then(response => {
        var temp = document.createElement("img");
        temp.src = "https://smart-webpage-images.s3.us-east-2.amazonaws.com/user_icon.png";
        responseBox.appendChild(temp);
        temp = document.createElement("p");
        temp.innerHTML = textFieldBox.value;
        responseBox.appendChild(temp);
        temp = document.createElement("img");
        temp.src = "https://smart-webpage-images.s3.us-east-2.amazonaws.com/chatbot_icon.jpg";
        responseBox.appendChild(temp);
        temp = document.createElement("p");
        temp.innerHTML = response;
        responseBox.appendChild(temp);
       })
    .catch(error => {
        // Handle error
        alert('Error submitting form' + error);
    });
});

async function getFileList(dir){
    const name = nameMatch[1];
    const response = await fetch(`/get_query_file_names?param=${dir}&faculty=${name}`);
    const data = await response.json();
    return data;
}

audioButton.addEventListener('click', function (event){
    event.preventDefault();
    if(audio_recording===false){
        recognition.start();
        audio_recording = true;
        this.innerText = "Stop";
    }
    else{
        recognition.stop();
        audio_recording = false;
        this.innerText = "Record";
    }
});

document.addEventListener('DOMContentLoaded', function (event) {
    const name = nameMatch[1];
    console.log(name);
    fetch(`/get_chat_history/${name}`, {
        method: "GET"
    })
    .then(response => response.json())
    //.then(response => JSON.stringify(response))
    .then(response => {
        if(response.length === 1 && response[0]==="Error fetching chat history"){
            var temp = document.createElement("p");
            temp.innerHTML = "Error fetching chat history";
            responseBox.appendChild(temp);
        }
        else{
            for(var i=0; i<response.length-1; i++){
                if(i%2===0){
                    var temp = document.createElement("img");
                    temp.src = "https://smart-webpage-images.s3.us-east-2.amazonaws.com/user_icon.png";
                    responseBox.appendChild(temp);
                    temp = document.createElement("p");
                    temp.innerHTML = response[i];
                    responseBox.appendChild(temp);
                }
                else{
                    temp = document.createElement("img");
                    temp.src = "https://smart-webpage-images.s3.us-east-2.amazonaws.com/chatbot_icon.jpg";
                    responseBox.appendChild(temp);
                    temp = document.createElement("p");
                    temp.innerHTML = response[i];
                    responseBox.appendChild(temp);
                }
            }
        }
       })
    .catch(error => {
        // Handle error
        alert('Error obtaining chat history');
    });
});
