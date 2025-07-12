// Global variables
let currentUser = null;
let users = [];
let swapRequests = [];
let isAdmin = false;

// API base URL
const API_BASE_URL = 'http://localhost:5000/api';

// Helper function for API Calls
async function apiCall(endpoint, method = 'GET', data = null, requiresAuth = true) {
    const headers = {
        'Content-Type': 'application/json'
    };
    if (requiresAuth && currentUser) {
        headers['Authorization'] = `Bearer ${currentUser.token}`;
    }
    const options = {
        method: method,
        headers: headers
    };
    if (body) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/${endpoint}`, options);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || 'API call failed');
        }

        return data;
    } catch (error) {
        console.error('API call error:', error);
        alert(`Error: ${error.message}`);
        throw error; // Re-throw to handle it in the calling function
    }
}
    
// Initialize the app
document.addEventListener('DOMContentLoaded', async function() {
    loadData();
    setupEventListeners();
    showTab('profile');
});

function setupEventListeners() {
    document.getElementById('profileForm').addEventListener('submit', saveProfile);
    document.getElementById('searchSkill').addEventListener('input', searchSkills);
    
    // Check if user is admin (for demo purposes, we'll use a simple check)
    if (localStorage.getItem('isAdmin') === 'true') {
        isAdmin = true;
        document.getElementById('adminTab').style.display = 'block';
    }
}

function loadData() {
    // Load from localStorage for demo purposes
    users = JSON.parse(localStorage.getItem('skillSwapUsers') || '[]');
    swapRequests = JSON.parse(localStorage.getItem('skillSwapRequests') || '[]');
    currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    
    if (currentUser) {
        loadUserProfile();
    }
    
    displayUsers();
    displayRequests();
    updateAdminStats();
}

function saveData() {
    localStorage.setItem('skillSwapUsers', JSON.stringify(users));
    localStorage.setItem('skillSwapRequests', JSON.stringify(swapRequests));
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
}

function saveProfile(e) {
    e.preventDefault();
    
    const profileData = {
        id: currentUser?.id || Date.now(),
        name: document.getElementById('name').value,
        location: document.getElementById('location').value,
        profilePhoto: document.getElementById('profilePhoto').value,
        skillsOffered: document.getElementById('skillsOffered').value.split(',').map(s => s.trim()).filter(s => s),
        skillsWanted: document.getElementById('skillsWanted').value.split(',').map(s => s.trim()).filter(s => s),
        availability: document.getElementById('availability').value,
        isPublic: document.getElementById('isPublic').checked,
        createdAt: currentUser?.createdAt || new Date().toISOString()
    };

    if (currentUser) {
        const index = users.findIndex(u => u.id === currentUser.id);
        if (index !== -1) {
            users[index] = profileData;
        } else {
            users.push(profileData);
        }
    } else {
        users.push(profileData);
    }

    currentUser = profileData;
    saveData();
    displayUsers();
    alert('Profile saved successfully!');
}

function loadUserProfile() {
    if (!currentUser) return;
    
    document.getElementById('name').value = currentUser.name || '';
    document.getElementById('location').value = currentUser.location || '';
    document.getElementById('profilePhoto').value = currentUser.profilePhoto || '';
    document.getElementById('skillsOffered').value = currentUser.skillsOffered?.join(', ') || '';
    document.getElementById('skillsWanted').value = currentUser.skillsWanted?.join(', ') || '';
    document.getElementById('availability').value = currentUser.availability || 'weekends';
    document.getElementById('isPublic').checked = currentUser.isPublic !== false;
}

function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to selected nav tab
    event.target.classList.add('active');
    
    // Refresh data for specific tabs
    if (tabName === 'browse') {
        displayUsers();
    } else if (tabName === 'requests') {
        displayRequests();
    } else if (tabName === 'admin') {
        displayAdminPanel();
    }
}

function displayUsers() {
    const userList = document.getElementById('userList');
    const publicUsers = users.filter(user => user.isPublic && user.id !== currentUser?.id);
    
    if (publicUsers.length === 0) {
        userList.innerHTML = '<p>No public users found. Create your profile first!</p>';
        return;
    }

    userList.innerHTML = publicUsers.map(user => `
        <div class="user-card">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                ${user.profilePhoto ? `<img src="${user.profilePhoto}" alt="Profile" style="width: 50px; height: 50px; border-radius: 50%; margin-right: 15px; object-fit: cover;">` : ''}
                <div>
                    <h3>${user.name}</h3>
                    ${user.location ? `<p style="color: #666;">📍 ${user.location}</p>` : ''}
                    <p style="color: #666;">🕒 Available: ${user.availability}</p>
                </div>
            </div>
            
            <div>
                <strong>Skills Offered:</strong>
                <div class="skills-tags">
                    ${user.skillsOffered?.map(skill => `<span class="skill-tag">${skill}</span>`).join('') || 'None'}
                </div>
            </div>
            
            <div>
                <strong>Skills Wanted:</strong>
                <div class="skills-tags">
                    ${user.skillsWanted?.map(skill => `<span class="skill-tag" style="background: linear-gradient(45deg, #e74c3c, #c0392b);">${skill}</span>`).join('') || 'None'}
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <button class="btn" onclick="sendSwapRequest(${user.id})">Send Swap Request</button>
            </div>
        </div>
    `).join('');
}

function searchSkills() {
    const searchTerm = document.getElementById('searchSkill').value.toLowerCase();
    const userCards = document.querySelectorAll('.user-card');
    
    userCards.forEach(card => {
        const skillTags = card.querySelectorAll('.skill-tag');
        let hasMatch = false;
        
        skillTags.forEach(tag => {
            if (tag.textContent.toLowerCase().includes(searchTerm)) {
                hasMatch = true;
            }
        });
        
        if (hasMatch || searchTerm === '') {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function sendSwapRequest(targetUserId) {
    if (!currentUser) {
        alert('Please create your profile first!');
        return;
    }
    
    const mySkill = prompt('Which of your skills would you like to offer?');
    const wantedSkill = prompt('Which skill would you like to learn?');
    
    if (mySkill && wantedSkill) {
        const request = {
            id: Date.now(),
            from: currentUser.id,
            to: targetUserId,
            mySkill: mySkill.trim(),
            wantedSkill: wantedSkill.trim(),
            status: 'pending',
            createdAt: new Date().toISOString()
        };
        
        swapRequests.push(request);
        saveData();
        alert('Swap request sent successfully!');
    }
}

function displayRequests() {
    displaySentRequests();
    displayReceivedRequests();
    displayCompletedSwaps();
}

function displaySentRequests() {
    const sentRequestsDiv = document.getElementById('sentRequests');
    const sent = swapRequests.filter(req => req.from === currentUser?.id);
    
    if (sent.length === 0) {
        sentRequestsDiv.innerHTML = '<p>No sent requests.</p>';
        return;
    }

    sentRequestsDiv.innerHTML = sent.map(req => {
        const targetUser = users.find(u => u.id === req.to);
        return `
            <div class="swap-request">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <div>
                        <strong>To: ${targetUser?.name || 'Unknown'}</strong>
                        <span class="status-badge status-${req.status}">${req.status.toUpperCase()}</span>
                    </div>
                    ${req.status === 'pending' ? `<button class="btn btn-danger" onclick="deleteSwapRequest(${req.id})">Delete</button>` : ''}
                </div>
                <p>Offering: <strong>${req.mySkill}</strong></p>
                <p>Wanting: <strong>${req.wantedSkill}</strong></p>
                <p style="color: #666; font-size: 12px;">Sent: ${new Date(req.createdAt).toLocaleDateString()}</p>
            </div>
        `;
    }).join('');
}

function displayReceivedRequests() {
    const receivedRequestsDiv = document.getElementById('receivedRequests');
    const received = swapRequests.filter(req => req.to === currentUser?.id);
    
    if (received.length === 0) {
        receivedRequestsDiv.innerHTML = '<p>No received requests.</p>';
        return;
    }

    receivedRequestsDiv.innerHTML = received.map(req => {
        const fromUser = users.find(u => u.id === req.from);
        return `
            <div class="swap-request">
                <div>
                    <strong>From: ${fromUser?.name || 'Unknown'}</strong>
                    <span class="status-badge status-${req.status}">${req.status.toUpperCase()}</span>
                </div>
                <p>They offer: <strong>${req.mySkill}</strong></p>
                <p>They want: <strong>${req.wantedSkill}</strong></p>
                <p style="color: #666; font-size: 12px;">Received: ${new Date(req.createdAt).toLocaleDateString()}</p>
                
                ${req.status === 'pending' ? `
                    <div style="margin-top: 10px;">
                        <button class="btn btn-success" onclick="respondToRequest(${req.id}, 'accepted')">Accept</button>
                        <button class="btn btn-danger" onclick="respondToRequest(${req.id}, 'rejected')">Reject</button>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function displayCompletedSwaps() {
    const completedSwapsDiv = document.getElementById('completedSwaps');
    const completed = swapRequests.filter(req => req.status === 'accepted' && 
        (req.from === currentUser?.id || req.to === currentUser?.id));
    
    if (completed.length === 0) {
        completedSwapsDiv.innerHTML = '<p>No completed swaps to rate.</p>';
        return;
    }

    completedSwapsDiv.innerHTML = completed.map(req => {
        const otherUser = users.find(u => u.id === (req.from === currentUser?.id ? req.to : req.from));
        return `
            <div class="swap-request">
                <div>
                    <strong>Swap with: ${otherUser?.name || 'Unknown'}</strong>
                    <span class="status-badge status-accepted">COMPLETED</span>
                </div>
                <p>Skills exchanged: <strong>${req.mySkill}</strong> ↔ <strong>${req.wantedSkill}</strong></p>
                
                ${!req.rating ? `
                    <div style="margin-top: 10px;">
                        <button class="btn" onclick="rateSwap(${req.id})">Rate This Swap</button>
                    </div>
                ` : `
                    <div style="margin-top: 10px;">
                        <div class="rating-stars">${'★'.repeat(req.rating)}${'☆'.repeat(5-req.rating)}</div>
                        <p style="font-style: italic;">"${req.feedback}"</p>
                    </div>
                `}
            </div>
        `;
    }).join('');
}

function deleteSwapRequest(requestId) {
    if (confirm('Are you sure you want to delete this swap request?')) {
        swapRequests = swapRequests.filter(req => req.id !== requestId);
        saveData();
        displayRequests();
    }
}

function respondToRequest(requestId, response) {
    const request = swapRequests.find(req => req.id === requestId);
    if (request) {
        request.status = response;
        saveData();
        displayRequests();
        alert(`Request ${response}!`);
    }
}

function rateSwap(requestId) {
    const rating = prompt('Rate this swap (1-5 stars):');
    const feedback = prompt('Leave feedback (optional):');
    
    if (rating && rating >= 1 && rating <= 5) {
        const request = swapRequests.find(req => req.id === requestId);
        if (request) {
            request.rating = parseInt(rating);
            request.feedback = feedback || '';
            saveData();
            displayRequests();
            alert('Thank you for your feedback!');
        }
    }
}

function displayAdminPanel() {
    updateAdminStats();
    displayAdminUsers();
    displayAdminSwaps();
}

function updateAdminStats() {
    document.getElementById('totalUsers').textContent = users.length;
    document.getElementById('totalSwaps').textContent = swapRequests.length;
    document.getElementById('pendingSwaps').textContent = swapRequests.filter(req => req.status === 'pending').length;
    document.getElementById('activeUsers').textContent = users.filter(u => u.isPublic).length;
}

function displayAdminUsers() {
    const adminUserList = document.getElementById('adminUserList');
    
    adminUserList.innerHTML = users.map(user => `
        <div class="user-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4>${user.name}</h4>
                    <p>Skills: ${user.skillsOffered?.length || 0} offered, ${user.skillsWanted?.length || 0} wanted</p>
                    <p>Status: ${user.isPublic ? 'Public' : 'Private'}</p>
                </div>
                <div>
                    <button class="btn btn-secondary" onclick="toggleUserStatus(${user.id})">
                        ${user.isPublic ? 'Make Private' : 'Make Public'}
                    </button>
                    <button class="btn btn-danger" onclick="deleteUser(${user.id})">Delete</button>
                </div>
            </div>
        </div>
    `).join('');
}

function displayAdminSwaps() {
    const adminSwapList = document.getElementById('adminSwapList');
    
    adminSwapList.innerHTML = swapRequests.map(req => {
        const fromUser = users.find(u => u.id === req.from);
        const toUser = users.find(u => u.id === req.to);
        return `
            <div class="swap-request">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${fromUser?.name || 'Unknown'} → ${toUser?.name || 'Unknown'}</strong>
                        <span class="status-badge status-${req.status}">${req.status.toUpperCase()}</span>
                    </div>
                    <button class="btn btn-danger" onclick="deleteSwapRequest(${req.id})">Delete</button>
                </div>
                <p>Skill exchange: ${req.mySkill} ↔ ${req.wantedSkill}</p>
                <p style="color: #666; font-size: 12px;">Created: ${new Date(req.createdAt).toLocaleDateString()}</p>
            </div>
        `;
    }).join('');
}

function toggleUserStatus(userId) {
    const user = users.find(u => u.id === userId);
    if (user) {
        user.isPublic = !user.isPublic;
        saveData();
        displayAdminUsers();
        displayUsers();
    }
}

function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user? This will also delete all their swap requests.')) {
        users = users.filter(u => u.id !== userId);
        swapRequests = swapRequests.filter(req => req.from !== userId && req.to !== userId);
        saveData();
        displayAdminUsers();
        displayUsers();
        displayRequests();
        updateAdminStats();
    }
}