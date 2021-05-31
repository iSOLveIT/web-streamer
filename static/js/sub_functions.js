
let all_normal_msg = document.querySelectorAll(".info-normal");
let all_success_msg = document.querySelectorAll(".info-success");
let all_danger_msg = document.querySelectorAll(".info-danger");
let all_notice = document.querySelectorAll(".info-notice");

if (all_normal_msg){
all_normal_msg.forEach(function(normal_msg){
    normal_msg.classList.add("low");
    setTimeout(function() {
        normal_msg.style.display = "none";
    }, 3000);
})
}

if (all_success_msg){
all_success_msg.forEach(function(success_msg){
    success_msg.classList.add("low");
    setTimeout(function() {
        success_msg.style.display = "none";
    }, 3000);
})
}

if (all_danger_msg){
all_success_msg.forEach(function(danger_msg){
    danger_msg.classList.add("low");
    setTimeout(function() {
        danger_msg.style.display = "none";
    }, 3000);
})
}
if (all_notice){
all_notice.forEach(function(notice){
    notice.classList.add("low");
    setTimeout(function() {
        notice.style.display = "none";
    }, 3000);
})
}