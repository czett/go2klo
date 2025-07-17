
// app stats number flow
function appStatsAnimation() {
    const appStatsBox = document.querySelector(".app-stats-block");

    if (!appStatsBox) {
        console.error("Element with class 'app-stats-block' not found.");
        return;
    }

    appStatsBox.childNodes.forEach((appStat) => {
        if (appStat.nodeType === Node.ELEMENT_NODE) {
            const valueTextElement = appStat.firstElementChild;

            if (valueTextElement && valueTextElement.dataset.value) {
                const finalValue = parseInt(valueTextElement.dataset.value);
                const appendText = valueTextElement.dataset.appendText || '';

                let currentValue = 0;
                const duration = 2000;
                const startTime = performance.now();

                function animateValue() {
                    const now = performance.now();
                    const progress = (now - startTime) / duration;

                    if (progress < 1) {
                        currentValue = Math.min(finalValue, Math.ceil(finalValue * progress));
                        valueTextElement.innerHTML = `${currentValue}${appendText}`;
                        requestAnimationFrame(animateValue);
                    } else {
                        currentValue = finalValue;
                        valueTextElement.innerHTML = `${currentValue}${appendText}`;
                    }
                }

                requestAnimationFrame(animateValue);
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", appStatsAnimation);
appStatsAnimation();