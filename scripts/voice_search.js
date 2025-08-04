document.addEventListener("DOMContentLoaded", function () {
    const micButton = document.getElementById("micButton");
    const searchInput = document.getElementById("searchInput");
    const searchForm = document.getElementById("searchForm");

    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.lang = "en-IN";
        recognition.interimResults = false;
        recognition.continuous = false;

        micButton.addEventListener("click", () => {
            recognition.start();
        });

        recognition.onresult = function (event) {
            const transcript = event.results[0][0].transcript;
            searchInput.value = transcript;
            searchForm.submit();
        };

        recognition.onerror = function (event) {
            alert("Speech recognition error: " + event.error);
        };
    } else {
        micButton.disabled = true;
        micButton.title = "Your browser doesn't support voice search.";
    }
});
