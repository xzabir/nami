document.addEventListener('DOMContentLoaded', () => {
    const introSplash = document.getElementById('intro-splash');
    
    // Dismiss the splash screen after the animation completes
    setTimeout(() => {
        introSplash.classList.add('hidden');
    }, 2800);

    const form = document.getElementById('nami-form');
    const urlInput = document.getElementById('video-url');
    
    const heroSection = document.getElementById('hero-section');
    const resultsView = document.getElementById('results-view');
    const captionsGrid = document.getElementById('captions-grid');
    const resetBtn = document.getElementById('reset-btn');
    
    const videoOverlay = document.getElementById('video-overlay');
    const bgVideo = document.getElementById('bg-video');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const videoUrl = urlInput.value.trim();
        if (!videoUrl) return;

        // Transition to loading state
        form.classList.add('loading');
        captionsGrid.innerHTML = '';

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    styles: ["formal", "sarcastic", "humorous_tech", "humorous_non_tech"]
                })
            });

            let data;
            const contentType = response.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                data = await response.json();
            } else {
                const text = await response.text();
                throw new Error(`Server error (${response.status}): ${text.slice(0, 120)}`);
            }

            if (!response.ok) {
                throw new Error(data.error || `Request failed with status ${response.status}`);
            }

            // Success: Play video background
            bgVideo.src = videoUrl;
            videoOverlay.classList.add('active');

            // Transition UI
            heroSection.classList.add('hidden');
            setTimeout(() => {
                resultsView.classList.add('active');
                renderResults(data.captions);
            }, 800);

        } catch (error) {
            heroSection.classList.add('hidden');
            setTimeout(() => {
                resultsView.classList.add('active');
                captionsGrid.innerHTML = `<div class="error-text">An error occurred: ${error.message}</div>`;
            }, 800);
        } finally {
            form.classList.remove('loading');
        }
    });

    resetBtn.addEventListener('click', () => {
        // Reset the UI
        resultsView.classList.remove('active');
        videoOverlay.classList.remove('active');
        
        setTimeout(() => {
            bgVideo.pause();
            bgVideo.removeAttribute('src');
            urlInput.value = '';
            heroSection.classList.remove('hidden');
            urlInput.focus();
        }, 1000);
    });

    function renderResults(captions) {
        if (!captions || Object.keys(captions).length === 0) {
            captionsGrid.innerHTML = `<div class="error-text">No captions returned.</div>`;
            return;
        }

        const styles = [
            { key: 'formal', label: 'Formal' },
            { key: 'sarcastic', label: 'Sarcastic' },
            { key: 'humorous_tech', label: 'Tech Humor' },
            { key: 'humorous_non_tech', label: 'Casual Humor' }
        ];

        let html = '';
        styles.forEach((style, index) => {
            const text = captions[style.key];
            if (text) {
                const delay = index * 0.15;
                html += `
                    <div class="caption-item" style="animation-delay: ${delay}s">
                        <div class="style-label">${style.label}</div>
                        <div class="style-text">${text}</div>
                    </div>
                `;
            }
        });

        captionsGrid.innerHTML = html;
    }
});
