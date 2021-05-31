var isMobile = /iPhone|iPad|iPod|Android/.test(navigator.userAgent);
var info_box = document.querySelector('.info');
var schedule_box = document.querySelector('.schedule');
var titles_box = document.querySelectorAll('.titles');
if (isMobile == true){
    info_box.setAttribute('class', 'col-12 info mb-2' );
    schedule_box.setAttribute('class', 'col-12 schedule mb-4' );
    titles_box.forEach(function(item){
        item.setAttribute('class', 'col-12 titles');
    })
}
else{
    info_box.setAttribute('class', 'col-7 info' );
    schedule_box.setAttribute('class', 'col-5 schedule' );
    titles_box.forEach(function(item){
        item.setAttribute('class', 'col-7 titles');
    })
}


const meetingDate = document.getElementById('inputStart');
let today = new Date();
let n_month = parseInt(today.getMonth()) + 1;
let n_day = today.getDate();

if (n_day < 10) {
    n_day = `0${n_day}`;
}
if (n_month < 10) {
    n_month = `0${n_month}`;
}

let minDate = `${today.getFullYear()}-${n_month}-${n_day}`;
meetingDate.setAttribute("min", `${minDate}`);

const copy_btn = document.querySelector('.btn-copy');

if (copy_btn != null){
    copy_btn.addEventListener('click', function(){
        const paragraph = document.querySelector('#meeting_text');
        navigator.clipboard.writeText(paragraph.value)
            .then(() => {
                document.querySelector(".text-copied").textContent = "Text Copied";
                document.querySelector(".text-copied").classList.add('info-success', 'low');
                    setTimeout(function() {
                        if (document.querySelector(".text-copied")){
                            document.querySelector(".text-copied").classList.remove('info-success', 'low');
                            document.querySelector(".text-copied").textContent = "";
                        }
                    }, 3000);
    
            })
            .catch(err => {
                paragraph.select();
                document.execCommand('copy');
                document.querySelector(".text-copied").textContent = "Text Copied";
                document.querySelector(".text-copied").classList.add('info-success', 'low');
                    setTimeout(function() {
                        if (document.querySelector(".text-copied")){
                            document.querySelector(".text-copied").classList.remove('info-success', 'low');
                            document.querySelector(".text-copied").textContent = "";
                        }
                    }, 3000);
            });
    })
}


function closeCover(){
    let close_cover = document.getElementById("close-cover");
    close_cover.addEventListener('click', function(){
        var m_cover = document.querySelector('.meeting_cover');
        m_cover.style.display = "none";
        show_details = "false";
        meeting_details = "";
        if (isMobile==true){
                document.body.style.overflow = auto;
            }
    })
}
