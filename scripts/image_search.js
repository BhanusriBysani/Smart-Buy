function submitImageSearch() {
    const fileInput = document.getElementById('cameraInput');
    const formData = new FormData();
    formData.append('image', fileInput.files[0]);

    fetch('/image_search', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())  // or .json() if you return JSON
    .then(html => {
        document.open();
        document.write(html);
        document.close();
    })
    .catch(error => console.error('Image search failed:', error));
}
