document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const formData = new FormData();
    formData.append('file', document.getElementById('file-upload').files[0]);

    fetch('http://127.0.0.1:8000/upload_csv/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('File processed:', data);
        alert('File processed successfully!');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error processing file!');
    });
});

document.getElementById('get-user').addEventListener('click', function() {
    const userId = document.getElementById('user-id').value;
    const fields = 'name,age,target';  // Change this to display different fields

    fetch(`http://127.0.0.1:8000/user/${userId}/?fields=${fields}`)
    .then(response => response.json())
    .then(data => {
        const userDetails = document.getElementById('user-details');
        userDetails.innerHTML = JSON.stringify(data.user_info, null, 2);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error retrieving user info!');
    });
});
