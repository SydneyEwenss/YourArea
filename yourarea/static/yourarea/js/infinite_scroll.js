let page = 2;  // Start loading from page 2
const postContainer = document.getElementById('post-container');
const loadingIndicator = document.getElementById('loading');

// Detect scroll event
window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
        if (!loadingIndicator.style.display || loadingIndicator.style.display === 'none') {
            loadingIndicator.style.display = 'block';
            loadMorePosts();
        }
    }
});

function loadMorePosts() {
    // Log the page number to ensure it's correct
    console.log('Loading more posts for page', page);

    fetch(`/?page=${page}&tab=all`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Received data:', data); // Debugging: Log the response

        // If no HTML content, stop the scroll
        if (data.html.trim() === '') {
            console.log("No more posts to load.");
            loadingIndicator.style.display = 'none';
            window.removeEventListener('scroll', loadMorePosts);
            return;
        }

        // Create a div to hold the new posts
        const newPosts = document.createElement('div');
        newPosts.innerHTML = data.html.trim();

        // Log the number of new posts being added
        console.log("New posts added:", newPosts.children.length);

        // Append the new posts to the container
        postContainer.appendChild(newPosts);

        // Hide the loading indicator and increment the page
        loadingIndicator.style.display = 'none';
        page++;

        // If fewer than 10 posts were returned, stop loading more
        if (newPosts.children.length < 10) {
            console.log("Last page loaded, stopping infinite scroll.");
            window.removeEventListener('scroll', loadMorePosts); // Stop infinite scroll
        }
    })
    .catch(error => {
        console.error("Error loading more posts:", error);
        loadingIndicator.style.display = 'none';  // Hide loading on error
    });
}
