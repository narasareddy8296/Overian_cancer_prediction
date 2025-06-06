function openTab(tabName) {
    const tabs = document.getElementsByClassName('tab-content');
    const buttons = document.getElementsByClassName('tab-btn');
    
    for (let tab of tabs) {
        tab.classList.remove('active');
    }
    
    for (let btn of buttons) {
        btn.classList.remove('active');
    }
    
    document.getElementById(tabName).classList.add('active');
    event.currentTarget.classList.add('active');
}

// Image preview functionality
document.getElementById('image').addEventListener('change', function(e) {
    const preview = document.getElementById('preview');
    const file = e.target.files[0];
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; height: auto; border-radius: 10px;">`;
        }
        reader.readAsDataURL(file);
    }
});
