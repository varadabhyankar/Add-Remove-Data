const options = document.getElementById('options');
const textFieldContainer = document.getElementById('textFieldContainer');
const newSelectContainer = document.getElementById('newSelectContainer');
const linksContainer = document.getElementById('linksContainer');
const submitButton = document.getElementById('submitButton');
const textFieldLabel = document.getElementById('textLabel');
const selectBox = document.getElementById('newSelect');
const deleteTextLabel = document.getElementById('deleteSelect');
const textFieldBox = document.getElementById('textField');
const fileSelectContainer = document.getElementById('fileSelectContainer')

options.addEventListener('change', function () {
    const selectedOption = options.value;

    // Reset all fields and button visibility
    textFieldContainer.style.display = 'none';
    newSelectContainer.style.display = 'none';
    linksContainer.style.display = 'none';
    submitButton.style.display = 'inline-block';
    selectBox.innerHTML = '';
    fileSelectContainer.style.display = 'none';

    if (['upload_general', 'upload_course', 'upload_research'].includes(selectedOption)) {
        if(selectedOption==="upload_research"){
            textFieldContainer.style.display = 'block';
            textFieldBox.required = true;
            textFieldBox.maxlength = "100";
            textFieldBox.placeholder = "Maximum 100 characters"
            textFieldLabel.innerHTML = "Enter the research paper name";
        }
        else if(selectedOption==="upload_course"){
            textFieldContainer.style.display = 'block';
            textFieldBox.required = true;
            textFieldBox.maxlength = "50";
            textFieldBox.placeholder = "Maximum 50 characters";
            textFieldLabel.innerHTML = "Enter the course name";
        }
        fileSelectContainer.style.display = 'block';
        submitButton.textContent = 'Submit';
    } else if (['delete_research', 'delete_course'].includes(selectedOption)) {
        submitButton.textContent = 'Delete';
        newSelectContainer.style.display = 'block'; // Show new select
        if(selectedOption==="delete_course"){
            deleteTextLabel.innerHTML = "Course to be deleted:";
            getFileList("course").then(file_list=> {
                for( let file_name of file_list){
                    console.log(file_name);
                    let opt = document.createElement('option');
                    opt.value = file_name;
                    opt.innerText = file_name;
                    selectBox.appendChild(opt);
                }
            });
        }
        else if(selectedOption==="delete_research"){
            deleteTextLabel.innerHTML = "Paper to be deleted:";
            getFileList("research").then(file_list=> {
                for( let file_name of file_list){
                    console.log(file_name);
                    let opt = document.createElement('option');
                    opt.value = file_name;
                    opt.innerText = file_name;
                    selectBox.appendChild(opt);
                }
            });
        }
    } else if (selectedOption === 'view') {
        submitButton.style.display = 'none'; // Hide button
        linksContainer.innerHTML = "";
        linksContainer.style.display = 'block'; // Show links
        let break_line = document.createElement("br");
        let course_list = document.createElement('p');
        course_list.innerHTML = "<b>General Information:</b><p>general_research.csv</p>" 
        linksContainer.appendChild(course_list);
        getFileList("course").then(file_list=> {
            let course_list = document.createElement('p');
            course_list.innerHTML = "<b>Course List:</b>"
            linksContainer.appendChild(course_list);
            for( let file_name of file_list){
                let list_element = document.createElement('p');
                list_element.innerText = file_name;
                linksContainer.appendChild(list_element);
            }
        });
        getFileList("research").then(file_list=> {
            let res_list = document.createElement('p');
            res_list.innerHTML = "<b>Research Paper List:</b>"
            linksContainer.appendChild(res_list);
            for( let file_name of file_list){
                let list_element = document.createElement('p');
                list_element.innerText = file_name;
                linksContainer.appendChild(list_element);
            }
        });
    }
});

function handleFileSelect(event){
    console.log(event);
    const file = event.target.files[0];
    if (file) {
        const allowedTypes = ['text/csv', 'application/vnd.ms-excel'];
        if (!allowedTypes.includes(file.type)) {
            document.getElementById("fileSelect").value = null;
            alert('Only CSV files are allowed');
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            document.getElementById("fileSelect").value = null;
            alert('File size exceeds 5MB limit');
            return;
        }
    }
    console.log("File satisfies the requirements");
    return;
}

async function getFileList(dir){
    const response = await fetch(`/get_file_names?param=${dir}`);
    const data = await response.json();
    return data;
}

async function handleLogout(){
    const response = await fetch('/logout');
    location.reload();
}