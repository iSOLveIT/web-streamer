const socket = io('/meeting');  // Initialize SocketIO

// Send chats messages button
const desktopSendBtn = document.getElementById('desktop_send_btn');
const mobileSendBtn = document.getElementById('mobile_send_btn');

// Leave or exit Class by host
const hostDesktopLeaveBtn = document.getElementById('host_desktop_leave_btn');
const hostMobileLeaveBtn = document.getElementById('host_mobile_leave_btn');

// Leave or exit Class by student
const studentDesktopLeaveBtn = document.getElementById('viewer_desktop_leave_btn');
const studentMobileLeaveBtn = document.getElementById('viewer_mobile_leave_btn');


socket.on('connect', () => {
  socket.emit('join-room', { room_id: ROOM_ID, user_id: USER_ID, user_name: USERNAME });
});


// handle the add member event
socket.on('add_member', data => {
  // Add participant name and increase count as they join
  let users_counts = document.querySelectorAll(".users_counts");
  let member_spaces = document.querySelectorAll(".member-space");
  // let old_member_spaces = document.querySelectorAll(".member-space p, .member-space hr");

  // // Remove the participant id if they exist to prevent duplicates
  // for (member=0; member<old_member_spaces.length; member++){
  //   if (old_member_spaces[member].textContent == `${data}`){
  //     old_member_spaces[member].remove();
  //     old_member_spaces[parseInt(member+1)].remove();
  //   }
  // }
  // Add the participant id
  member_spaces[0].innerHTML += add_member_desktop(data);
  member_spaces[1].innerHTML += add_member_mobile(data);

  users_counts.forEach(function (user_count){
    user_count.textContent = parseInt(user_count.textContent) + 1;
  })
});

// handle list of participants who have joined meeting
socket.on('add_members', data => {
  // Add participant name and increase count as they join
  let users_counts = document.querySelectorAll(".users_counts");
  let member_spaces = document.querySelectorAll(".member-space");

  let participants = data;

  for (i in participants){
    member_spaces[0].innerHTML += add_member_desktop(participants[i]);
    member_spaces[1].innerHTML += add_member_mobile(participants[i]);
    }

  users_counts.forEach(function (user_count){
    user_count.textContent = participants.length;
  })
});


// handle the remove member event
socket.on('remove_member', data => {
  // Remove participant name and decrease count as they leave
  let member_spaces = document.querySelectorAll(".member-space p, .member-space hr");

  for (member=0; member<member_spaces.length; member++){
    if (member_spaces[member].textContent == `${data}`){
      member_spaces[member].remove();
      member_spaces[parseInt(member+1)].remove();
    }
  }
  if (isMobile == true){
    let mobile_members = document.querySelectorAll(".participants_feature .member-space p");
    let users_counts = document.querySelector("#users_btn span.users_counts");
    users_counts.textContent = mobile_members.length;
    }
  else{
    let desktop_members = document.querySelectorAll("li.dropdown .member-space p");
    let users_counts = document.querySelector("span.bg-counter.users_counts");
    users_counts.textContent = desktop_members.length;
  }
  

});


socket.on('server_response', data => {
  console.log(data.result);
});

socket.on('class_end', () =>{
    // If host ends class
    student_leave();
})

socket.on('room_notice', data => {
  let notice = document.querySelectorAll(".message");
  let isHandheldDevice = /iPhone|iPad|iPod|Android/.test(navigator.userAgent);
  if (isHandheldDevice==true){
    let item = notice[1];
    item.innerHTML = data;
    item.classList.add('info-notice');
    item.classList.remove('message');
    item.style.display = "block";

    
  }
  else{
    let item = notice[0];
    item.innerHTML = data;
    item.classList.add('info-notice');
    item.classList.remove('message');
    item.style.display = "block";
  }
});



// Room Broadcast
socket.on('receive_room_message', data => {
  let roomMsgBox = document.querySelectorAll(".chat-space");
  // Add message to msg_board
  roomMsgBox.forEach(function(room_box){
    let paragraph = user_msg(data.sender, data.msg, chatSentAt());
    room_box.innerHTML += paragraph;
  })
});

// Send chats from desktop
desktopSendBtn.addEventListener('click', function () {
  let roomMsgBox = document.querySelectorAll(".chat-space");
  let msg = document.querySelector('.desktop_msg_area').value;
  let isEmpty = /^[\n\t\ ]*?$/.test(msg)
  if (isEmpty != true){
    // Add message to msg_board
    roomMsgBox.forEach(function(room_box){
      let paragraph = host_msg(USERNAME, msg, chatSentAt());
      room_box.innerHTML += paragraph;
    })
    // send message to room
    broadcast_msg(msg);
    // Clear text area
    document.querySelector('.desktop_msg_area').value = "";
  }
})

// Send chats from mobile device
mobileSendBtn.addEventListener('click', function () {
  let roomMsgBox = document.querySelectorAll(".chat-space"); 
  let msg = document.querySelector('.mobile_msg_area').value;
  let isEmpty = /^[\n\t\ ]*?$/.test(msg)
  if (isEmpty != true){
    // Add message to msg_board
    roomMsgBox.forEach(function(room_box){
      let paragraph = host_msg(USERNAME, msg, chatSentAt());
      room_box.innerHTML += paragraph;
    })
    // send message to room
    broadcast_msg(msg);
    // Clear text area
    document.querySelector('.mobile_msg_area').value = "";
  }
})
/* Route for leaving class */

// Tasks to perform on student leaving class
var student_leave = function(){
  window.localStorage.removeItem("v_hours");
  window.localStorage.removeItem("v_seconds");
  window.localStorage.removeItem("v_minutes");
  
  leave_room();
  window.location.replace("/join_meeting/v/user_verify");
}

// Tasks to perform on host leaving class
var host_leave = function(){
  socket.emit('notice', { room_id: ROOM_ID, msg: "Class ended by Host"});

  window.localStorage.removeItem("s_hours");
  window.localStorage.removeItem("s_seconds");
  window.localStorage.removeItem("s_minutes");

  close_room();
  leave_room();
  window.location.replace(`/attendance_report/${ROOM_ID}`);
}

// Student leaves Class
if (studentDesktopLeaveBtn != null || studentMobileLeaveBtn != null){
  studentDesktopLeaveBtn.addEventListener('click', function () {student_leave()});
  studentMobileLeaveBtn.addEventListener('click', function () {student_leave()});
}
// Host leaves Class
if (hostDesktopLeaveBtn != null || hostMobileLeaveBtn != null){
  hostDesktopLeaveBtn.addEventListener('click', function () {host_leave()});
  hostMobileLeaveBtn.addEventListener('click', function () {host_leave()});
}



function broadcast_msg(message) {
  socket.emit('send_room_message', { room_id: ROOM_ID, msg: `${message}`, sender: USERNAME});
}

// Leave Room
function leave_room() {
  socket.emit('leave-room', { room_id: ROOM_ID, user_id: USER_ID });
  // window.location.replace("new target URL");
}

// Close Room
function close_room() {
  socket.emit('close-room', { room_id: ROOM_ID, user_id: USER_ID });
}

function host_msg(sender, message, time_sent) {
  return `<p class="fw-normal p-2 host-message mt-2"> <b>${sender}</b> @ <em>${time_sent}</em><br>${message}</p>`
}

function user_msg(sender, message, time_sent) {
  return `<p class="fw-normal p-2 member-message mt-2"> <b>${sender}</b> @ <em>${time_sent}</em><br>${message}</p>`
}


function add_member_mobile(member_id) {
  return "<p class=\"fw-bold p-2\">" + `${member_id}` + "</p><hr>"
}

function add_member_desktop(member_id) {
  return " <p class=\"dropdown-item\">" + `${member_id}` + "</p><hr class=\"dropdown-divider\">"
}

function chatSentAt() {
    var date = new Date();
    var hours = date.getHours();
    var minutes = date.getMinutes();

    // Check whether AM or PM
    var new_format = hours >= 12 ? 'pm' : 'am';

    // Find current hour in AM-PM Format
    hours = hours % 12;

    // To display "0" as "12"
    hours = hours ? hours : 12;
    minutes = minutes < 10 ? '0' + minutes : minutes;

    let result = hours + ':' + minutes + ' ' + new_format;

    return result
}

// window.addEventListener('beforeunload', () => {
//   var formData = new FormData();
//   formData.append('room_id', ROOM_ID);
//   formData.append('user_id', USERNAME);

//   var url = '/'
//   navigator.sendBeacon(url, formData);

//   if (!navigator.sendBeacon) {
//   navigator.sendBeacon = (url, formData) =>
//     window.fetch(url, {method: 'POST', body: formData});
//   }
// });



// function user_msg(sender, message, time_sent) {
//   if (/[\w+\s\,\'\"\:\;\>\<\?\\/\$\@\#\%\^\&\*\(\)\-\+\=\|\}\{\]\[\.\~\`]{30,}?/.test(message)) {
//     return " <p class=\"users text-white font-weight-light bg-dark border border-dark p-2\"> " +
//       `<strong class="text-warning font-weight-bold">${sender}</strong> <br>` +
//       `${message}` + " </p> "
//   }
//   return " <p class=\"users text-white font-weight-light bg-dark border border-dark p-2\" style=\"width: max-content\"> " +
//     `<strong class="text-warning font-weight-bold">${sender}</strong> <br>` +
//     `${message}` + " </p> "
// }

/*
let jk = document.querySelectorAll('.member-space p');
jk.forEach(function(user){
  if (user.textContent == '10087873'){
    user.remove();
  }
  update_count.textContent = jk.length - 1;
*/
// handle the json event sent with socket.send()
// socket.on('json', data => {
//   console.log(data.msg);
// });


// socket.on('username', data => {
//   let header = document.createElement("h1");
//   header.textContent = USERNAME;
//   divUserName.appendChild(header);
// });