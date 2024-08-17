import { showMessage } from './messages.js';

// Function to toggle the password update form visibility
export function togglePasswordForm() {
    const updatePasswordForm = document.getElementById('updatePasswordForm');
    if (updatePasswordForm.style.display === 'none' || updatePasswordForm.style.display === '') {
        updatePasswordForm.style.display = 'flex';
        updatePasswordForm.style.flexDirection = 'column';
    } else {
        updatePasswordForm.style.display = 'none';
    }
}

// Function to handle the password update process
export function handlePasswordUpdate(userData) {
    document.getElementById('updatePasswordForm').addEventListener('submit', (event) => {
        event.preventDefault();
        const newPassword = document.getElementById('newPassword').value;
        if (!newPassword) {
            console.error('Password cannot be empty');
            return;
        }

        fetch(`/user/${userData.id}/`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${userData.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: newPassword })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Password updated successfully:', data);
            showMessage('Password updated successfully', '#ProfileModal', 'accept');
            document.getElementById('newPassword').value = '';
            document.getElementById('updatePasswordForm').style.display = 'none';
        })
        .catch(error => {
            console.error('Error updating password:', error);
            showMessage('Error updating password', '#ProfileModal', 'error');
            document.getElementById('newPassword').value = '';
        });
    });
}
