document.addEventListener('DOMContentLoaded', function() {
    const generateBtn = document.getElementById('generateBtn');
    const copyBtn = document.getElementById('copyBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const preview = document.getElementById('preview');
    const spinner = document.getElementById('spinner');
    const errorDiv = document.getElementById('error');
    const outputInfo = document.getElementById('outputInfo');
    
    const helpBtn = document.getElementById('helpBtn');
    const helpBtnHeader = document.getElementById('helpBtnHeader');
    const helpModal = document.getElementById('helpModal');
    const closeHelp = document.getElementById('closeHelp');
    const closeHelpBtn = document.getElementById('closeHelpBtn');
    const tryDemoBtn = document.getElementById('tryDemoBtn');
    
    let currentReadme = '';
    let projectName = 'README';
    
    function openHelpModal() {
        helpModal.classList.add('active');
        setTimeout(() => {
            document.querySelectorAll('.tutorial-step').forEach((step, index) => {
                setTimeout(() => {
                    step.classList.add('visible');
                }, index * 200);
            });
        }, 300);
    }
    
    function closeHelpModal() {
        helpModal.classList.remove('active');
    }
    
    helpBtn.addEventListener('click', openHelpModal);
    helpBtnHeader?.addEventListener('click', openHelpModal);
    closeHelp.addEventListener('click', closeHelpModal);
    closeHelpBtn.addEventListener('click', closeHelpModal);
    
    helpModal.addEventListener('click', function(e) {
        if (e.target === helpModal) {
            closeHelpModal();
        }
    });
    
    const demoTree = `my-awesome-project/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── utils.py
│   └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_utils.py
├── docs/
│   ├── API.md
│   └── README.md
├── .gitignore
├── requirements.txt
├── setup.py
└── README.md`;
    
    tryDemoBtn.addEventListener('click', function() {
        closeHelpModal();
        
        document.getElementById('treeInput').value = demoTree;
        document.getElementById('author').value = 'John Doe';
        document.getElementById('username').value = 'johndoe';
        
        const treeInput = document.getElementById('treeInput');
        treeInput.style.animation = 'focusRing 0.5s ease';
        setTimeout(() => {
            treeInput.style.animation = '';
        }, 500);
        
        setTimeout(() => {
            generateBtn.click();
        }, 300);
    });
    
    generateBtn.addEventListener('click', async function() {
        const tree = document.getElementById('treeInput').value;
        const template = document.getElementById('template').value;
        const author = document.getElementById('author').value;
        const username = document.getElementById('username').value;
        
        if (!tree.trim()) {
            showError('Please paste a folder tree first.');
            return;
        }
        
        hideError();
        generateBtn.disabled = true;
        spinner.style.display = 'block';
        preview.textContent = '';
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tree: tree,
                    template: template,
                    author: author,
                    github_username: username
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Generation failed');
            }
            
            const data = await response.json();
            currentReadme = data.readme;
            projectName = data.readme.split('\n')[0]?.replace(/^#\s*/, '') || 'README';
            
            preview.textContent = currentReadme;
            
            outputInfo.style.display = 'grid';
            document.getElementById('langInfo').innerHTML = '<strong>Language:</strong> ' + (data.language || 'Unknown');
            document.getElementById('typeInfo').innerHTML = '<strong>Type:</strong> ' + (data.type || 'Unknown');
            document.getElementById('licenseInfo').innerHTML = '<strong>License:</strong> ' + (data.license || 'None');
            
            copyBtn.disabled = false;
            downloadBtn.disabled = false;
            
        } catch (error) {
            showError(error.message);
            copyBtn.disabled = true;
            downloadBtn.disabled = true;
        } finally {
            generateBtn.disabled = false;
            spinner.style.display = 'none';
        }
    });
    
    copyBtn.addEventListener('click', async function() {
        if (!currentReadme) return;
        
        try {
            await navigator.clipboard.writeText(currentReadme);
            copyBtn.textContent = 'Copied!';
            setTimeout(() => {
                copyBtn.textContent = 'Copy';
            }, 2000);
        } catch (err) {
            showError('Failed to copy to clipboard');
        }
    });
    
    downloadBtn.addEventListener('click', function() {
        if (!currentReadme) return;
        
        const blob = new Blob([currentReadme], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = projectName + '.md';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
    
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    function hideError() {
        errorDiv.style.display = 'none';
    }
    
    window.copyToClipboard = async function(text) {
        try {
            await navigator.clipboard.writeText(text);
            showToast('Copied to clipboard!');
        } catch (err) {
            showToast('Failed to copy');
        }
    };
    
    function showToast(message) {
        let toast = document.querySelector('.toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'toast';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 2500);
    }
});