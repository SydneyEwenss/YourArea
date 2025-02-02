// Load posts when scrolling down
window.addEventListener('scroll', function() {
    const bottomOfPage = document.documentElement.scrollHeight === document.documentElement.scrollTop + window.innerHeight;
    if (bottomOfPage) {
        loadMorePosts();
    }
});

let currentPage = 1;
let loading = false;

// This function will be called when the user scrolls to the bottom of the page
function loadMorePosts() {
    const currentPage = getCurrentPage();  // You'll need to define how to track the current page
    const url = `/load_more_posts/?page=${currentPage}`;  // URL for your load_more_posts view

    // Send an AJAX GET request to the server
    fetch(url)
        .then(response => response.json())  // Parse JSON response
        .then(data => {
            if (data.posts) {
                appendPosts(data.posts);  // Function to append posts to the DOM
                updateCurrentPage();  // Function to update the current page number
            } else {
                console.error("No posts data received");
            }
        })
        .catch(error => {
            console.error("Error loading posts:", error);
        });
}

// Call this function to append the posts to your existing posts container
function appendPosts(posts) {
    const postsContainer = document.getElementById("posts-container");  // Your posts container
    posts.forEach(post => {
        const postElement = createPostElement(post);  // Function to create a post's HTML
        postsContainer.appendChild(postElement);  // Add the post to the container
    });
}

// Function to create HTML for each post (adjust based on your post model)
function createPostElement(post) {
    const postElement = document.createElement("div");
    postElement.classList.add("post");
    
    postElement.innerHTML = `
        <div class="post-content">${post.content}</div>
        <div class="post-date">${post.created_at}</div>
    `;
    
    return postElement;
}

// Function to get the current page (you might already be doing this in your code)
function getCurrentPage() {
    // You can store the current page in a global variable or get it from the URL
    const urlParams = new URLSearchParams(window.location.search);
    return parseInt(urlParams.get('page') || 1);
}

// Function to update the current page (increment it after loading more posts)
function updateCurrentPage() {
    const currentPage = getCurrentPage();
    const newPage = currentPage + 1;
    const newUrl = new URL(window.location.href);
    newUrl.searchParams.set('page', newPage);
    window.history.pushState({}, '', newUrl);
}

// Call loadMorePosts when the user scrolls to the bottom of the page
window.addEventListener("scroll", function() {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight) {
        loadMorePosts();
    }
});
