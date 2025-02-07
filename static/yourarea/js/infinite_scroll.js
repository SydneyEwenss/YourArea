let page = 2;  // Start loading from page 2
const postContainer = document.getElementById('post-container');
const loadingIndicator = document.getElementById('loading');

// Detect scroll event
window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
        loadingIndicator.style.display = 'block';
        loadMorePosts();
    }
});

function loadMorePosts() {
    fetch(`/?page=${page}&tab=all`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html.trim() === '') {
            // No more posts to load, stop the infinite scroll
            loadingIndicator.style.display = 'none';
            window.removeEventListener('scroll', loadMorePosts);
            return;
        }

        // Create a div to hold the new posts
        const newPosts = document.createElement('div');
        newPosts.innerHTML = data.html.trim();

        // Append the new posts to the container
        postContainer.appendChild(newPosts);

        // Hide the loading indicator and increment the page
        loadingIndicator.style.display = 'none';
        page++;

        // If fewer than 10 posts were returned, stop loading more
        if (newPosts.children.length < 10) {
            window.removeEventListener('scroll', loadMorePosts); // Stop infinite scroll
        }
    })
    .catch(() => {
        loadingIndicator.style.display = 'none';  // Hide loading on error
    });
}
