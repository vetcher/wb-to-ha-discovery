document.addEventListener('DOMContentLoaded', () => {
    const copyButton = document.getElementById('copyButton');
    const yamlContent = document.getElementById('yamlContent');

    // Initial fetch of YAML content
    fetch('/api/wb_to_ha.yaml')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then(text => {
            yamlContent.textContent = text;
        })
        .catch(error => {
            console.error('Error fetching YAML:', error);
            yamlContent.textContent = 'Error loading YAML content. Please try again later.';
        });

    copyButton.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(yamlContent.textContent);

            // Visual feedback
            const originalText = copyButton.textContent;
            copyButton.textContent = 'Copied!';
            copyButton.style.backgroundColor = '#45a049';

            setTimeout(() => {
                copyButton.textContent = originalText;
                copyButton.style.backgroundColor = '#4CAF50';
            }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
            copyButton.textContent = 'Failed to copy';
            copyButton.style.backgroundColor = '#f44336';

            setTimeout(() => {
                copyButton.textContent = 'Copy';
                copyButton.style.backgroundColor = '#4CAF50';
            }, 2000);
        }
    });
});