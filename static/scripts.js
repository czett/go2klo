// js from base template
function mobileMenu(){
    iconBtn = document.querySelector(".menu-icon");
    // let state = iconBtn.dataset.collapsed;

    if (iconBtn.dataset.collapsed == "1"){
        document.querySelector(".links").style.visibility = "visible";
        document.querySelector(".lang-list").style.visibility = "visible";
        document.querySelector(".menu-icon-span").style.rotate = "90deg";
        iconBtn.dataset.collapsed = "0";
    }else{
        document.querySelector(".links").style.visibility = "hidden";
        document.querySelector(".lang-list").style.visibility = "hidden";
        document.querySelector(".menu-icon-span").style.rotate = "0deg";
        iconBtn.dataset.collapsed = "1";
    }
}

function toggleLangs(){
    langsBtn = document.querySelector(".mobile-lang-btn");
    // let state = iconBtn.dataset.collapsed;

    if (langsBtn.dataset.collapsed == "1"){
        document.querySelector(".lang-switch").style.transform = "translate(-50%, 50%)";
        langsBtn.dataset.collapsed = "0";
    }else{
        document.querySelector(".lang-switch").style.transform = "translate(-50%, -50%)";
        langsBtn.dataset.collapsed = "1";
    }
}

function notiToggler(){
    const box = document.querySelector(".notifications-box");

    if (box.dataset.collapsed == "1"){
        box.style.visibility = "visible";
        box.dataset.collapsed = "0";
    }else{
        box.style.visibility = "hidden";
        box.dataset.collapsed = "1";
    }
}

function hideLoader() {
    const loader = document.querySelector(".loading-box");
    if (loader) {
        loader.classList.add("hidden");
    }
}

window.addEventListener("load", hideLoader);

// "pageshow" wird auch beim Zurückgehen ausgelöst
window.addEventListener("pageshow", (event) => {
    // Wenn die Seite aus dem BFCache (Back-Forward Cache) geladen wurde
    if (event.persisted) {
        hideLoader();
    }
});

document.querySelectorAll("a").forEach(link => {
link.addEventListener("click", e => {
    const href = link.getAttribute("href");

    if (href && !href.startsWith("#") && !href.startsWith("javascript") && link.target !== "_blank"){
        const loader = document.querySelector(".loading-box");

        // only shows loader when loading takes quite a whiole (750ms is okay locally, maybe more eventually for prod?)
        const showLoaderTimeout = setTimeout(() => {
            loader.classList.add("visible");
        }, 500);
    }
});
});

// several js funcs collected from subpages
function disableRatedWindow(){
    document.querySelector(".rated-banner").style.display = "none";
}

function redirect(url) {
    // window.location.href = url;

    // loader implementation
    const loader = document.querySelector(".loading-box");
    if (!loader) return;

    loader.classList.remove("hidden");
    loader.classList.add("visible");
    
    // console.log("soy gurt");

    setTimeout(() => {
        window.location.href = url;
    }, 300);
}

function updateValue(id, value) {
    document.getElementById(id).textContent = value;
}

function like(ratingId) {
    fetch('/api/like-rating/' + ratingId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the like icon or count here if needed
            // console.log('Rating liked successfully:');
            document.getElementById('like-icon-span-'+ratingId).classList.toggle('liked'); // Toggle liked class for visual feedback
        } /*else {
            console.error('Error liking the rating:', data.error);
        }*/
    })
    .catch(error => console.error('Error:', error));
}

// display amount of files uploaded on img upload when rating toilet
function updateUploadCounter(inp, toReplaceClass) {
    let files = inp.files;
    let len = files.length;

    document.querySelector("." + toReplaceClass).innerHTML = "" + len;

    if (len > 0) {
        var file = files[0];
        var reader = new FileReader();
        
        reader.onload = function(e) {
            var img = new Image();
            img.onload = function() {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                const MAX_WIDTH = 300;
                const MAX_HEIGHT = 300;
                let width = img.width;
                let height = img.height;

                if (width > height) {
                    if (width > MAX_WIDTH) {
                        height *= MAX_WIDTH / width;
                        width = MAX_WIDTH;
                    }
                } else {
                    if (height > MAX_HEIGHT) {
                        width *= MAX_HEIGHT / height;
                        height = MAX_HEIGHT;
                    }
                }

                canvas.width = width;
                canvas.height = height;
                ctx.drawImage(img, 0, 0, width, height);
                const compressedBase64 = canvas.toDataURL('image/jpeg', 0.7);

                // set dummy ta value to base64 img
                var textarea_dummy = document.querySelector("#b64-img");
                textarea_dummy.value = compressedBase64;

                // console.log("Compressed image size:", compressedBase64.length);
            }
            img.src = e.target.result;
        };    
        reader.readAsDataURL(file);
    }

    return;
}

// gambling page!!!!

function spinWheel(){
    // const spin = 360;
    const spin = 360 + (Math.random() * 2000);
    const wheel = document.querySelector(".wheel-of-fortune");

    wheel.style.rotate = "" + spin + "deg";
    wheel.style.pointerEvents = "none";

    // im such a genius for coming up w/ this
    let dest = "";
    if (spin % 360 < 20 || spin % 360 > 340){
        // console.log("win");
        dest = "w";
    }else{
        // console.log("loser");
        dest = "l";
    }

    setTimeout(() => {
        let gamble_dest = "/gambling/" + dest;
        redirect(gamble_dest);
    }, 6000);

    return;
}

// flush or pass

function flushOrPass(action){
    const image = document.querySelector(".fop-box img");
    filename = parseInt(image.dataset.filename);

    if (filename <= 4){
        image.dataset.filename = filename + 1;
    }else{
        image.dataset.filename = 1;
        filename = 0;
    }

    image.src = `/static/img/fop/${filename + 1}.png`;   
}

function toggleEditRatingWindow(){
    const editWindow = document.querySelector(".edit-rating-window");
    const isVisible = editWindow.style.display === "block";

    if (isVisible) {
        editWindow.style.display = "none";
    } else {
        editWindow.style.display = "block";
    }
}