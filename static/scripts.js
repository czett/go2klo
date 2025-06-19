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

// loading page when loading done (fade out :3)
window.addEventListener("load", () => {
    const loader = document.querySelector(".loading-box");
    
    if (loader){
        loader.classList.add("hidden");
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
            console.log('Rating liked successfully:');
            document.getElementById('like-icon-span-'+ratingId).classList.toggle('liked'); // Toggle liked class for visual feedback
        } else {
            console.error('Error liking the rating:', data.error);
        }
    })
    .catch(error => console.error('Error:', error));
}