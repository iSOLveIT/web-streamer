// Student ID Validate
function Student(){
    let user_id = document.getElementById("inputID");
    let validate_box = document.querySelector('span.id_num');
    user_id.addEventListener('input', function(){
       let isCorrect = /^10[0-9]{6}$/.test(user_id.value);
       let validate = user_id.value == ""? "" : isCorrect == true ? "✓ Correct ID Number" : "✖ Wrong ID Number";
       validate_box.textContent = validate;
    })
}
// Meeting ID Validate
function Meeting(){
    let meeting_id = document.getElementById("inputMeetingID");
    let meeting_validate_box = document.querySelector('span.meet_id');
    let isCorrect = /^[a-zA-Z0-9]{5}$/.test(meeting_id.value);
    let validate = meeting_id.value == "" ? "" : isCorrect == true ? "✓ Valid Meeting ID" : "✖ Invalid Meeting ID";
    meeting_validate_box.textContent = validate;

    meeting_id.addEventListener('input', function(){
        let isCorrect = /^[a-zA-Z0-9]{5}$/.test(meeting_id.value);
        let validate = meeting_id.value == "" ? "" : isCorrect == true ? "✓ Valid Meeting ID" : "✖ Invalid Meeting ID";
        meeting_validate_box.textContent = validate;
    })
}
