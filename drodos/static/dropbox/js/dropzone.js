var dropzone;

function setup() {
    dropzone = select('#dropzone');
    dropzone.dragOver(highlight);
    dropzone.dragLeave(unhighlight);

    dropzone.elt.addEventListener ("drop", dropFile, false);

    jQuery(document).ready(function ($) {
    $('#dropzone').on("dragenter dragstart dragend dragleave dragover drag drop", function (e) {
        e.preventDefault();
    });
    });
}

function mouseClick() {
    var input = document.getElementById("filesInputId");
    console.log(input);

    var dp = document.getElementById("dropzone");
    dp.submit();
}

function highlight() {
    dropzone.class('dropzone dragOver');
}

function unhighlight() {
    dropzone.class('dropzone');
}

function dropFile(ev) {
    unhighlight.call();
    var files = ev.dataTransfer.files;
    var dp = document.getElementById("dropzone");
    var formData = new FormData(dp);

    for(file of files){
        formData.append('filesInputId', file);
    }

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload2/', true);

    xhr.addEventListener('readystatechange', function(e) {
    if (xhr.readyState == 4 && xhr.status == 200) {
      // Done. Inform the user
        console.log('success');
        window.location.href = xhr.responseURL;
    }
    else if (xhr.readyState == 4 && xhr.status != 200) {
      // Error. Inform the user
        alert('something went wrong');
        console.log('error');
    }
    });
    xhr.send(formData);
}

function gotFile(file) {
}

//Problems: Loading... message