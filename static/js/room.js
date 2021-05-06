const socket = io('/meeting');

//const privateBtn = document.getElementById('p_msg_btn');
const broadcastBtn = document.getElementById('msg_btn');


let roomMsgBox = document.getElementById('all_b_msg');
let divUserName = document.getElementById('user_name');



socket.on('connect', () => {
  // socket.emit('store_user_credential', { client_id: socket.id });
  // socket.emit('store_room_user_credential', { room_id: ROOM_ID, client_id: socket.id });
  socket.emit('join-room', { room_id: ROOM_ID, user_id: USERNAME});

});

socket.on('username', data => {
  let header = document.createElement("h1");
  header.textContent = USERNAME;
  divUserName.appendChild(header);
});

// handle the message event sent with socket.send()
socket.on('message', data => {
  let paragraph = notification(data);
  roomMsgBox.innerHTML += paragraph;
});

// handle the json event sent with socket.send()
socket.on('json', data => {
  console.log(data.msg);
});

socket.on('server_response', data => {
  console.log(data.result);
});

// Room Broadcast
socket.on('receive_room_message', data => {
  let paragraph = user_msg(data.sender, data.msg);
  roomMsgBox.innerHTML += paragraph;
});

broadcastBtn.addEventListener('click', function () {
  let msg = document.getElementById('msgTextarea').value;
  // Add message to msg_board
  let paragraph = host_msg(msg);
  roomMsgBox.innerHTML += paragraph;
  // Clear text area
  document.getElementById('msgTextarea').value = "";
  // send message to room
  broadcast_msg(msg);

})

function broadcast_msg(message) {
  socket.emit('send_room_message', { room_id: ROOM_ID, msg: `${message}`, sender: USERNAME });
}


// Leave Room
function leave_room() {
  socket.emit('leave-room', { room_id: ROOM_ID, user_id: USERNAME });
}

function host_msg(message) {
  if (/[\w+\s\,\'\"\:\;\>\<\?\\/\$\@\#\%\^\&\*\(\)\-\+\=\|\}\{\]\[\.\~\`]{30,}?/.test(message)) {

    return " <p class=\"hosts text-dark font-weight-light bg-warning border border-warning p-2\"> " +
      `${message}` + " </p> "
  }
  return " <p class=\"hosts text-dark font-weight-light bg-warning border border-warning p-2\" style=\"width: max-content\"> " +
    `${message}` + " </p> "
}

function user_msg(sender, message) {
  if (/[\w+\s\,\'\"\:\;\>\<\?\\/\$\@\#\%\^\&\*\(\)\-\+\=\|\}\{\]\[\.\~\`]{30,}?/.test(message)) {
    return " <p class=\"users text-white font-weight-light bg-dark border border-dark p-2\"> " +
      `<strong class="text-warning font-weight-bold">${sender}</strong> <br>` +
      `${message}` + " </p> "
  }
  return " <p class=\"users text-white font-weight-light bg-dark border border-dark p-2\" style=\"width: max-content\"> " +
    `<strong class="text-warning font-weight-bold">${sender}</strong> <br>` +
    `${message}` + " </p> "
}

function notification(message) {
  return " <p class=\"text-center\"> " +
    `<strong class="text-success font-weight-bold">${message}</strong>` + " </p> "
}

// socket.on('disconnect', (reason) => {
//   socket.emit('leave-room', {room_id: ROOM_ID, client_id: socket.id});
//   localStorage.removeItem(`${socket.id}`);
//   console.log("Disconnected!!");
// });