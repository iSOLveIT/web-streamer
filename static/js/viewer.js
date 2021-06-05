var wheel_btn = document.getElementById('main_btn');
var wheel_btn_symbol = document.querySelector('#main_btn i');
var action_contacts = document.querySelector('.btn-wheel_action_contacts');
wheel_btn.addEventListener('click', function () {
    let check = action_contacts.getAttribute('data-toggle');
    if (check == "off") {
        let animate_wheel_btn = document.querySelector('.btn-wheel_main');

        animate_wheel_btn.classList.remove('scale-up-center');
        animate_wheel_btn.classList.add('scale-down-center');

        action_contacts.style.display = "block";
        wheel_btn_symbol.className = "icon-close";
        action_contacts.setAttribute('data-toggle', "on");
    }
    else if (check == "on") {
        let animate_wheel_btn = document.querySelector('.btn-wheel_main');

        animate_wheel_btn.classList.remove('scale-down-center');
        animate_wheel_btn.classList.add('scale-up-center');

        action_contacts.style.display = "none";
        wheel_btn_symbol.className = "icon-menu";
        action_contacts.setAttribute('data-toggle', "off");
    }

})


var chats_btn = document.getElementById('chat_btn');
chats_btn.addEventListener('click', function () {
    let wheel_box = document.querySelector('.btn-wheel');
    let antmedia_box = document.querySelector(".antmedia_holder");
    let feature_box = document.querySelector(".feature_holder");
    let participant_feature = document.querySelector(".feature_holder .participants_feature");
    let chat_feature = document.querySelector(".feature_holder .chats_feature");
    

    wheel_box.style.display = "none";
    antmedia_box.style.height = "300px";
    feature_box.style.display = "block";
    participant_feature.style.display = "none";

    chat_feature.classList.remove('swing-out-top-bck');
    chat_feature.classList.add('tilt-in-fwd-tr');
    chat_feature.style.display = "block";

    chat_feature.setAttribute('data-feature', "on");
    participant_feature.setAttribute('data-feature', "off");
})

var close_chat_feature = document.querySelector('.close_chat_feature_btn');
close_chat_feature.addEventListener('click', function () {
    let animate_wheel_btn = document.querySelector('.btn-wheel_main');
    let wheel_btn_symbol = document.querySelector('#main_btn i');
    let wheel_box = document.querySelector('.btn-wheel');
    let antmedia_box = document.querySelector(".antmedia_holder");
    let feature_box = document.querySelector(".feature_holder");
    let chat_feature = document.querySelector(".feature_holder .chats_feature");
    let action_contacts = document.querySelector('.btn-wheel_action_contacts');
    let chat_toggle = chat_feature.getAttribute('data-feature');

    if (chat_toggle == "on") {
        chat_feature.classList.remove('tilt-in-fwd-tr');
        chat_feature.classList.add('swing-out-top-bck');
        chat_feature.style.display = "none";

        feature_box.style.display = "none";
        antmedia_box.style.height = "var(--app-content-height)";

        action_contacts.style.display = "none";
        action_contacts.setAttribute('data-toggle', "off");

        animate_wheel_btn.classList.remove('scale-down-center');
        animate_wheel_btn.classList.add('scale-up-center');
        wheel_btn_symbol.className = "icon-menu";

        wheel_box.style.display = "block";
        chat_feature.setAttribute('data-feature', "off");
    }
})


var users_btn = document.getElementById('users_btn');
users_btn.addEventListener('click', function () {
    let wheel_box = document.querySelector('.btn-wheel');
    let antmedia_box = document.querySelector(".antmedia_holder");
    let feature_box = document.querySelector(".feature_holder");
    let participant_feature = document.querySelector(".feature_holder .participants_feature");
    let chat_feature = document.querySelector(".feature_holder .chats_feature");

    wheel_box.style.display = "none";
    antmedia_box.style.height = "300px";
    feature_box.style.display = "block";
    chat_feature.style.display = "none";

    participant_feature.classList.remove('swing-out-top-bck');
    participant_feature.classList.add('tilt-in-fwd-tr');
    participant_feature.style.display = "block";
    participant_feature.setAttribute('data-feature', "on");
    chat_feature.setAttribute('data-feature', "off");

})


var close_user_feature = document.querySelector('.close_users_feature_btn');
close_user_feature.addEventListener('click', function () {
    let animate_wheel_btn = document.querySelector('.btn-wheel_main');
    let wheel_btn_symbol = document.querySelector('#main_btn i');
    let wheel_box = document.querySelector('.btn-wheel');
    let antmedia_box = document.querySelector(".antmedia_holder");
    let feature_box = document.querySelector(".feature_holder");
    let participant_feature = document.querySelector(".feature_holder .participants_feature");
    let action_contacts = document.querySelector('.btn-wheel_action_contacts');
    let participant_toggle = participant_feature.getAttribute('data-feature');

    if (participant_toggle == "on") {
        participant_feature.classList.remove('tilt-in-fwd-tr');
        participant_feature.classList.add('swing-out-top-bck');
        participant_feature.style.display = "none";

        feature_box.style.display = "none";
        antmedia_box.style.height = "var(--app-content-height)";

        action_contacts.style.display = "none";
        action_contacts.setAttribute('data-toggle', "off");

        animate_wheel_btn.classList.remove('scale-down-center');
        animate_wheel_btn.classList.add('scale-up-center');
        wheel_btn_symbol.className = "icon-menu";

        wheel_box.style.display = "block";
        participant_feature.setAttribute('data-feature', "off");
    }
})



var meeting_btn = document.getElementById('meeting_btn');
var meeting_info = document.querySelector('.meeting_details');
meeting_btn.addEventListener('click', function () {
    meeting_info.classList.remove('scale-out-tl');
    meeting_info.classList.add('scale-in-tl');
    meeting_info.style.display = "block";
})


document.body.addEventListener('click', function () {
    var meeting_info = document.querySelector('.meeting_details');
    let check = meeting_info.style.display;
    if (check == "block") {
        meeting_info.classList.remove('scale-in-tl');
        meeting_info.classList.add('scale-out-tl');
        meeting_info.style.display = "none";
    }
}, true);


var m_meeting_btn = document.getElementById('m_meeting_btn');
var m_meeting_info = document.querySelector('.m_meeting_details');
m_meeting_btn.addEventListener('click', function () {
    m_meeting_info.classList.remove('scale-out-tl');
    m_meeting_info.classList.add('scale-in-tl');
    m_meeting_info.style.display = "block";
})


document.body.addEventListener('click', function () {
    var m_meeting_info = document.querySelector('.m_meeting_details');
    let check = m_meeting_info.style.display;
    if (check == "block") {
        m_meeting_info.classList.remove('scale-in-tl');
        m_meeting_info.classList.add('scale-out-tl');
        m_meeting_info.style.display = "none";
    }
}, true)



// focus events don't bubble, must use capture phase
var isNotPC = /iPhone|iPad|iPod|Android/.test(navigator.userAgent);

if (isNotPC == true) {
    document.body.addEventListener("focus", event => {
        const target = event.target;
        switch (target.tagName) {
            case "INPUT":
            case "TEXTAREA":
            case "SELECT":
                document.getElementById("send-msg").classList.add("keyboard");
        }
    }, true);
    document.body.addEventListener("blur", () => {
        document.getElementById("send-msg").classList.remove("keyboard");
    }, true);
}



function startTimer(duration, display) {
    var timer = duration, hours, minutes, seconds;
    var refresh = setInterval(function () {
        var hrs = timer / 3600;
        var mins = (timer % 3600) / 60;
        var secs = (timer % 3600) % 60;

        hours = parseInt(hrs, 10);
        minutes = parseInt(mins, 10);
        seconds = parseInt(secs, 10);

        hours = hours < 10 ? "0" + hours : hours;
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        var output = hours + " : " + minutes + " : " + seconds;
        display.textContent = output;

        if (--timer < 0) {
            timer = duration;
            display.textContent = "Time's Up!";
            clearInterval(refresh);  // exit refresh loop

            student_leave();    // Execute function if class ends
//            window.localStorage.removeItem("v_hours");
//            window.localStorage.removeItem("v_seconds");
//            window.localStorage.removeItem("v_minutes");
//
//            // Leave meeting when time is up
//            leave_room();
//            window.location.replace("/join_meeting/v/user_verify");

        }
        window.localStorage.setItem("v_hours", hours);
        window.localStorage.setItem("v_seconds", seconds);
        window.localStorage.setItem("v_minutes", minutes);

    }, 1000);

}

window.onload = function () {
    var sec = parseInt(window.localStorage.getItem("v_seconds"));
    var min = parseInt(window.localStorage.getItem("v_minutes"));
    var hrs = parseInt(window.localStorage.getItem("v_hours"));

    if ((parseInt(hrs * min)) || (parseInt(hrs + min))) {
        var Second = (parseInt((hrs * 3600) + (min * 60)) + sec);
    }
    else if ((parseInt(min * sec)) || (parseInt(min + sec))) {
        var Second = (parseInt(min * 60) + sec);
    }
    else {
        var Second = SECONDS;
    }
    display = document.querySelectorAll('.time');
    display.forEach(function (item) {
        startTimer(Second, item);
    })
};


var isMobile = /iPhone|iPad|iPod|Android/.test(navigator.userAgent);
var desktop_iframe = document.querySelector('.desktop-iframe');
var mobile_iframe = document.querySelector('.mobile-iframe');
var add_iframe = `<iframe title="Video received" src="http://localhost:5080/LiveApp/play.html?id=${STREAM_ID}" allowfullscreen></iframe>`

if (isMobile == true) {
    desktop_iframe.innerHTML = "";
    mobile_iframe.innerHTML = add_iframe;
}
else {
    mobile_iframe.innerHTML = "";
    desktop_iframe.innerHTML = add_iframe;
}


// document.getElementById("exambtn").onclick = remove_items;

// function remove_items() {
//     window.localStorage.removeItem("seconds");
//     window.localStorage.removeItem("minutes");
// }

/*
let jk = document.querySelectorAll('.member-space p');
jk.forEach(function(user){
  if (user.textContent == '10087873'){
    user.remove();
  }
  update_count.textContent = jk.length - 1;
*/
// document.getElementById('quizForm').submit();
// alert("Time's Up!");