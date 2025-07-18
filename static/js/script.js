document.addEventListener("DOMContentLoaded", () => {
  // === Configuration ===
  const CONFIG = {
    // API configuration
    api: {
      protocol: 'http',
      host: window.location.hostname || 'localhost', // Use current hostname or default to localhost
      port: '5001',
      get baseUrl() {
        return `${this.protocol}://${this.host}:${this.port}`;
      }
    }
  };
  
  // For debugging
  console.log(`Using API endpoint: ${CONFIG.api.baseUrl}`);
  
  const thinkingBtnHero = document.getElementById('thinkingModeHeroBtn');
  const thinkingBtnChat = document.getElementById('thinkingModeChatBtn');
  let thinkingNewDefault = false;
  let thinkingStatusMap = {};

  function updateThinkingUI(status) {
    thinkingBtnHero.classList.toggle('active', status);
    thinkingBtnChat.classList.toggle('active', status);
  }

  function toggleThinkingMode() {
    const newStatus = !thinkingBtnHero.classList.contains('active');
    updateThinkingUI(newStatus);
    if (currentConversationId) {
      thinkingStatusMap[currentConversationId] = newStatus;
    } else {
      thinkingNewDefault = newStatus;
    }
  }

  thinkingBtnHero.addEventListener('click', toggleThinkingMode);
  thinkingBtnChat.addEventListener('click', toggleThinkingMode);


  // === Popup Handler ===
  const uploadBtn = document.getElementById('uploadDocBtn');
  const uploadButton = document.getElementById('uploadButton');
  const popup = document.getElementById('uploadPopup');
  const dropArea = document.getElementById('dropArea');
  const fileInput = document.getElementById('fileInput');
  const fileList = document.getElementById('fileList');
  const dropAreaText = document.getElementById('dropAreaText');
  const viewHistoryBtn = document.getElementById('viewHistoryBtn');
  const backToUploadBtn = document.getElementById('backToUploadBtn');
  const uploadView = document.getElementById('uploadView');
  const historyView = document.getElementById('historyView');
  let filesArray = []; 

  let uploadState = 'ready';

  uploadButton.addEventListener('click', async () => {
    if (uploadState === 'ready') {
      await uploadFiles();
    } else if (uploadState === 'done') {
      resetUploadUI();
    }
  });

  viewHistoryBtn.addEventListener('click', async () => {
    uploadView.style.display = 'none';
    historyView.style.display = 'block';
    await loadUploadHistory();
  });

  backToUploadBtn.addEventListener('click', () => {
    historyView.style.display = 'none';
    uploadView.style.display = 'block';
  });

  async function loadUploadHistory() {
    const res = await fetch(`${CONFIG.api.baseUrl}/upload/history`);
    const history = await res.json();
  
    const uploadedHistory = document.getElementById('uploadedHistory');
    uploadedHistory.innerHTML = '';
  
    history.forEach(item => {
      const historyItem = document.createElement('div');
      historyItem.innerHTML = `<span style="color: #10a37f;">• ${item.user_given_name} (${new Date(item.upload_time).toLocaleString()})</span>`;
      uploadedHistory.appendChild(historyItem);
    });
  }

  function validateBeforeUpload() {
    let allNamed = true;
    const inputs = fileList.querySelectorAll('.file-custom-name');
    inputs.forEach(input => {
      if (!input.value.trim()) {
        allNamed = false;
        input.style.border = '1px solid red'; 
      } else {
        input.style.border = '1px solid #ccc'; 
      }
    });
    return allNamed;
  }

  async function uploadFiles() {
    if (filesArray.length === 0) {
      alert('Vui lòng thêm ít nhất 1 file trước khi upload.');
      return;
    }
    if (!validateBeforeUpload()) {
      alert('Vui lòng nhập tên cho tất cả các tài liệu trước khi upload.');
      return;
    }
    
    uploadState = 'uploading';
    uploadButton.disabled    = true;
    uploadButton.textContent = 'Uploading...';

    const inputs      = fileList.querySelectorAll('.file-custom-name');
    const statusTexts = fileList.querySelectorAll('.upload-status-text');
    const deleteBtns  = fileList.querySelectorAll('.delete-file-btn');
    const addMoreBtn  = fileList.querySelector('.add-more-btn');

    deleteBtns.forEach(btn => btn.style.display = 'none');
    if (addMoreBtn) addMoreBtn.style.display = 'none';

    filesArray.forEach((_, i) => {
      statusTexts[i].textContent = 'Đang xử lý...';
    });

    const uploadPromises = filesArray.map((fileObj, i) => {
      const customName = inputs[i].value.trim();
      const formData   = new FormData();
      formData.append('file', fileObj);
      formData.append('name', customName);

      return fetch(`${CONFIG.api.baseUrl}/upload`, {
        method: 'POST',
        body: formData,
      }).then(async res => {
        const result = await res.json();
        statusTexts[i].textContent = res.ok ? '✓ Thành công' : '✗ Lỗi';
      }).catch(() => {
        statusTexts[i].textContent = '✗ Lỗi kết nối';
      });
    });

    await Promise.all(uploadPromises);
    uploadState = 'done';
    uploadButton.disabled    = false;
    uploadButton.textContent = 'Done';
  }

  function resetUploadUI() {
    uploadState = 'ready';
    filesArray = [];
    renderFileList();
    dropArea.style.display = 'flex';
    fileList.style.display  = 'none';
    uploadButton.textContent = 'Upload';
  }

  function renderFileList() {
    fileList.innerHTML = '';
  
    filesArray.forEach((file, index) => {
      const statusSpan = document.createElement('span');
      statusSpan.className = 'upload-status-text';
      statusSpan.textContent = ''; 
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
  
      const fileName = document.createElement('div');
      fileName.className = 'file-name';
      fileName.textContent = file.name;
  
      const customNameInput = document.createElement('input');
      customNameInput.className = 'file-custom-name';
      customNameInput.placeholder = 'Nhập tên văn bản';
      customNameInput.setAttribute('data-index', index);
  
      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'delete-file-btn';
      deleteBtn.textContent = 'Xóa';
      deleteBtn.onclick = () => {
        filesArray.splice(index, 1);
        if (filesArray.length === 0) {
          fileList.style.display = 'none';
          dropArea.style.display = 'flex';
        }
        renderFileList();
      };
  
      fileItem.appendChild(fileName);
      fileItem.appendChild(customNameInput);
      fileItem.appendChild(statusSpan);
      fileItem.appendChild(deleteBtn);
  
      fileList.appendChild(fileItem);
    });
  
    if (filesArray.length < 5) {
      const addMoreBtn = document.createElement('button');
      addMoreBtn.className = 'add-more-btn';
      addMoreBtn.textContent = 'Thêm dữ liệu';
      addMoreBtn.onclick = () => {
        fileInput.click();
      };
      fileList.appendChild(addMoreBtn);
    }
  }

  async function handleFiles(selectedFiles) {
    const remainingSlots = 5 - filesArray.length;
  
    if (selectedFiles.length > remainingSlots) {
      alert(`Bạn chỉ có thể thêm tối đa ${remainingSlots} file nữa.`);
    }
  
    const filesToCheck = [...selectedFiles].slice(0, remainingSlots);
  
    let uploadedNames = [];
    try {
      const res = await fetch(`${CONFIG.api.baseUrl}/upload/history`);
      const history = await res.json();
      uploadedNames = history.map(item => item.file_name); 
    } catch (err) {
      console.error('Không thể lấy lịch sử upload:', err);
    }
  
    const validFiles = filesToCheck.filter(file => {
      const notDuplicateInSession = !filesArray.some(f => f.name === file.name);
      const notDuplicateInHistory = !uploadedNames.includes(file.name);
      const isPDF = file.type === 'application/pdf';
      return notDuplicateInSession && notDuplicateInHistory && isPDF;
    });
  
    if (validFiles.length < filesToCheck.length) {
      alert('Một số file đã bị bỏ qua vì trùng tên hoặc không phải file PDF, hoặc đã upload trước đó.');
    }
  
    if (validFiles.length > 0) {
      filesArray.push(...validFiles);
      renderFileList();
      dropArea.style.display = 'none';
      fileList.style.display = 'flex';
    } else {
      if (filesArray.length === 0) {
        dropArea.style.display = 'flex';
        fileList.style.display = 'none';
      }
    }
  }

  dropArea.addEventListener('click', () => {
    fileInput.click();
  });

  dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.classList.add('dragover');
    dropAreaText.textContent = "Thả file vào đây";
  });

  dropArea.addEventListener('dragleave', () => {
    dropArea.classList.remove('dragover');
    dropAreaText.textContent = "Kéo dữ liệu vào đây";
  });

  dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.classList.remove('dragover');
    dropAreaText.textContent = "Kéo dữ liệu vào đây";

    if (e.dataTransfer.files.length) {
      handleFiles([...e.dataTransfer.files]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length) {
      handleFiles([...fileInput.files]);
      fileInput.value = ''; 
    }
  });

  uploadBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    popup.classList.toggle('open');
    console.log("ok")
  });

  document.addEventListener('mousedown', (e) => {
    const closeBtn = document.getElementById('closeUploadPopup');
    
    if (closeBtn && (e.target === closeBtn || closeBtn.contains(e.target))) {
      popup.classList.remove('open');
      return;
    }
  
    if (popup.contains(e.target) || uploadBtn.contains(e.target)) {
      return; 
    }
  
    popup.classList.remove('open'); 
  });
  // === State ===
  let conversations = [];
  let currentConversationId = null;
  let pendingStreams = {};  
  let statusMap = {};       
  let lastHeroSendTime = 0;

  // === DOM refs ===
  const sidebar               = document.getElementById('sidebar');
  const newChatBtn            = document.querySelector('.new-chat-btn');
  const mainContent           = document.getElementById('mainContent');
  const contentInner          = document.getElementById('contentInner');
  const chatInputContainer    = document.querySelector('.chat-input-container');
  const conversationContainer = document.getElementById('conversationContainer');
  const heroSection           = document.getElementById('heroSection');
  const searchInput           = document.querySelector('.search-input');
  const searchBtn             = document.querySelector('.search-btn');
  const chatInput             = document.querySelector('.chat-input');
  const chatSendBtn           = document.querySelector('.chat-send-btn');

  const API_BASE = CONFIG.api.baseUrl;

  // === Helpers ===
  function scrollToBottom() {
    conversationContainer.scrollTop = conversationContainer.scrollHeight;
  }
  function syncChatInputClass() {
    if (!chatInputContainer) return;
    if (sidebar.classList.contains('open')) {
      chatInputContainer.classList.add('open');
      chatInputContainer.classList.remove('close');
    } else {
      chatInputContainer.classList.add('close');
      chatInputContainer.classList.remove('open');
    }
  }
  function markSidebarLoading(id) {
    statusMap[id] = 'loading';
    const item = document.querySelector(`.chat-item[data-id="${id}"]`);
    if (item) {
      item.classList.add('loading');
      item.classList.remove('done');
    }
  }
  function markSidebarDone(id) {
    statusMap[id] = 'done';
    const item = document.querySelector(`.chat-item[data-id="${id}"]`);
    if (item) {
      item.classList.remove('loading');
      item.classList.add('done');
    }
  }

  // === Sidebar toggle ===
  window.toggleSidebar = function() {
    if (sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
      mainContent.classList.remove('open');
      contentInner.classList.remove('open');
      chatInputContainer.classList.remove('open');
      chatInputContainer.classList.add('close');
      sidebar.classList.add('close');
      mainContent.classList.add('close');
      contentInner.classList.add('close');
    } else {
      sidebar.classList.remove('close');
      mainContent.classList.remove('close');
      contentInner.classList.remove('close');
      chatInputContainer.classList.remove('close');
      chatInputContainer.classList.add('open');
      sidebar.classList.add('open');
      mainContent.classList.add('open');
      contentInner.classList.add('open');
    }
    syncChatInputClass();
  };

  chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
  });

  searchInput.addEventListener('input', function() {
    this.style.height = 'auto'; 
    this.style.height = (this.scrollHeight) + 'px'; 
  });

  // === Load sidebar list ===
  async function updateSidebar() {
    const res = await fetch(`${API_BASE}/conversations`);
    conversations = await res.json();
    const chatHistory = document.querySelector('.chat-history');
    chatHistory.innerHTML = '';
  
    conversations.forEach(conv => {
      const item = document.createElement('div');
      item.className = 'chat-item';
      item.dataset.id = conv.id;
  
      const title = document.createElement('span');
      title.className = 'chat-title';
      title.textContent = conv.title;
      item.appendChild(title);
  
      const del = document.createElement('button');
      del.className = 'delete-btn';
      del.innerText = '×';
      item.appendChild(del);
  
      if (statusMap[conv.id] === 'loading') {
        item.classList.add('loading');
      } else if (statusMap[conv.id] === 'done') {
        item.classList.add('done');
      }
  
      item.addEventListener('click', (e) => {
        if (e.target.classList.contains('delete-btn')) return; 
        if (statusMap[conv.id] === 'done') {
          delete statusMap[conv.id];
          item.classList.remove('done');
        }
        if (conv.id !== currentConversationId) {
          loadConversation(conv.id);
        }
      });
  
      del.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (!confirm('Bạn có chắc muốn xoá cuộc trò chuyện này?')) return;
        await fetch(`${API_BASE}/conversation/${conv.id}`, { method: 'DELETE' });
        await updateSidebar();
        if (currentConversationId === conv.id) {
          currentConversationId = null;
          conversationContainer.innerHTML = '';
          heroSection.style.display = 'block';
          conversationContainer.style.display = 'none';
          chatInputContainer.style.display = 'none';
          searchInput.style.height = '40px'
          searchInput.value = ''
        }
      });
      chatHistory.appendChild(item);
    });
    const activeEl = chatHistory.querySelector(`.chat-item[data-id="${currentConversationId}"]`);
    if (activeEl) activeEl.classList.add('active');
  }

  // === Load a conversation ===
  async function loadConversation(id) {
    currentConversationId = id;
    
    document.querySelectorAll('.chat-item').forEach(el => el.classList.remove('active'));
    const activeItem = document.querySelector(`.chat-item[data-id="${id}"]`);
    if (activeItem) activeItem.classList.add('active');
    if (pendingStreams[id]) {
      chatSendBtn.disabled = true;
    } else {
      chatSendBtn.disabled = false;
    }

    const res = await fetch(`${API_BASE}/conversation/${id}`);
    const conv = await res.json();

    conversationContainer.innerHTML = '';
    conv.messages.forEach(msg => addMessage(msg.content, msg.role));

    if (pendingStreams[id]) {
      addMessage(pendingStreams[id].userMessage, 'user');
      conversationContainer.appendChild(pendingStreams[id].botDiv);
    }

    scrollToBottom();
    heroSection.style.display = 'none';
    conversationContainer.style.display = 'block';
    chatInputContainer.style.display = 'flex';
    syncChatInputClass();

    const status = thinkingStatusMap[id] ?? false;
    updateThinkingUI(status);
  }

  function addMessage(content, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message ' + (sender === 'user' ? 'user-message' : 'bot-message');
  
    if (sender === 'user') {
      msgDiv.textContent = 'You: ' + content;
    } else {
      const thinkMatch = content.match(/<think>([\s\S]*?)<\/think>/i);
      let answer = content.replace(thinkMatch[0], '').trim();;
  
      if (thinkMatch) {
        const thinkingText = thinkMatch[1].trim();
        if (thinkingText) {
          answer = content.replace(thinkMatch[0], '').trim();
  
          const details = document.createElement('details');
          details.open = false;
  
          const summary = document.createElement('summary');
          summary.textContent = 'Đã suy nghĩ';
          summary.style.cursor     = 'pointer';
          summary.style.color      = '#949494';
          summary.style.fontWeight = '600';
          summary.style.fontSize = "14px";
  
          const pre = document.createElement('pre');
          pre.textContent     = thinkingText;
          pre.style.whiteSpace  = 'pre-wrap';
          pre.style.background  = '#f9f9f9';
          pre.style.padding     = '10px';
          pre.style.marginTop   = '6px';
          pre.style.borderRadius= '5px';
  
          details.appendChild(summary);
          details.appendChild(pre);
          msgDiv.appendChild(details);
        }
      }
  
      const answerDiv = document.createElement('div');
      answerDiv.style.marginTop = thinkMatch && thinkMatch[1].trim() ? '0' : '0';
      answerDiv.innerHTML = marked.parse(answer);
      msgDiv.appendChild(answerDiv);
    }
  
    conversationContainer.appendChild(msgDiv);
    scrollToBottom();
  }

  // === Streaming logic ===
  async function streamBotResponse(text) {
    const thisConvId = currentConversationId;

    if (pendingStreams[thisConvId]) return;
    chatSendBtn.disabled = true;

    addMessage(text, 'user');

    const botDiv = document.createElement('div');
    botDiv.className = 'message bot-message loading-blink';
    botDiv.textContent = 'Đang suy nghĩ...';
    conversationContainer.appendChild(botDiv);
    scrollToBottom();

    pendingStreams[thisConvId] = { userMessage: text, botDiv };
    markSidebarLoading(thisConvId);

    const enableThinking = thinkingStatusMap[thisConvId] ?? false;

    const startTime = Date.now();

    const res = await fetch(`${API_BASE}/conversation/${thisConvId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: text,
            index_name: 'text_embeddings',
            enable_thinking: enableThinking
        })
    });

    if (!res.body) {
        botDiv.textContent = 'Lỗi: không nhận được phản hồi từ server.';
    } else {
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let done = false, accumulated = '';
        let thinkingText = '';
        let answerText = '';
        let hasThought = false;

        while (!done) {
            const { value, done: doneReading } = await reader.read();
            done = doneReading;
            if (value) {
                accumulated += decoder.decode(value, { stream: true });

                // Tách <think> nếu có
                const thinkMatch = accumulated.match(/<think>([\s\S]*?)<\/think>/i);
                if (thinkMatch) {
                    thinkingText = thinkMatch[1].trim();
                    answerText = accumulated.replace(thinkMatch[0], '').trim();
                    hasThought = true;
                } else {
                    answerText = accumulated.trim();
                }

                // Update UI
                botDiv.innerHTML = '';

                if (enableThinking && thinkingText) {
                    botDiv.innerHTML += `<details open> <summary style="cursor:pointer; color:#949494; font-size:14px; font-weight:600;"></summary><pre style="white-space: pre-wrap; background: #f9f9f9; padding: 10px; border-radius: 5px;">${thinkingText}</pre></details>`;
                }

                // Câu trả lời chính
                botDiv.innerHTML += marked.parse(answerText);
                scrollToBottom();
            }
        }

        // Khi hoàn thành
        const totalSeconds = Math.round((Date.now() - startTime) / 1000);
        if (enableThinking && hasThought) {
            const summaryEl = botDiv.querySelector('summary');
            const detailsEl = botDiv.querySelector('details');
            if (summaryEl) {
                summaryEl.innerHTML = `Đã suy nghĩ trong ${totalSeconds} giây (bấm để xem)`;
            }
            // Auto đóng lại
            if (detailsEl) {
                detailsEl.removeAttribute('open');
            }
        }
    }

    botDiv.classList.remove('loading-blink');
    delete pendingStreams[thisConvId];
    markSidebarDone(thisConvId);

    await fetch(`${API_BASE}/conversations/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: thisConvId })
    });

    await updateSidebar();
    chatSendBtn.disabled = false;
}

  // === Hero search handler ===
  async function handleHeroQuestion() {
    const now = Date.now();
    if (now - lastHeroSendTime < 4000) {
      alert('Bạn đang gửi quá nhanh, vui lòng chờ một chút.');
      return;
    }
    lastHeroSendTime = now;
    const q = searchInput.value.trim();
    if (!q) return;
    const wordCount = q.split(/\s+/).length;
    if (wordCount > 104) {
      alert('Vui lòng nhập dưới 104 từ.');
      return;
    }
    isHeroAsking = true;
    if (!currentConversationId) {
      let previewTitle = q.length > 30 ? q.slice(0, 30) + '...' : q;
      const res = await fetch(`${CONFIG.api.baseUrl}/conversation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: previewTitle })
      });
      const { id } = await res.json();
      currentConversationId = id;
      thinkingStatusMap[currentConversationId] = thinkingNewDefault;
      updateThinkingUI(thinkingNewDefault);
      await fetch(`${CONFIG.api.baseUrl}/conversations/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      updateSidebar();
    }

    conversationContainer.innerHTML = '';
    heroSection.style.display = 'none';
    conversationContainer.style.display = 'block';
    chatInputContainer.style.display = 'flex';
    syncChatInputClass();
  
    await streamBotResponse(q);
  }

  // === Bottom input handler ===
  async function handleChatInput() {
    const text = chatInput.value.trim();
    if (!text) return;
    const wordCount = text.split(/\s+/).length;
    if (wordCount > 104) {
      alert('Vui lòng nhập dưới 104 từ.');
      return;
    };
    chatInput.value = '';
    chatInput.style.height = '40px';
    await streamBotResponse(text);
  }

  // === Events ===
  searchBtn.addEventListener('click', handleHeroQuestion);
  searchInput.addEventListener('keyup', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleHeroQuestion();
    }
  });
  chatSendBtn.addEventListener('click', handleChatInput);
  chatInput.addEventListener('keyup', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!chatSendBtn.disabled){
        handleChatInput();
      }
    }
  });
  newChatBtn.addEventListener('click', () => {
    currentConversationId = null;
    conversationContainer.innerHTML = '';
    heroSection.style.display = 'block';
    conversationContainer.style.display = 'none';
    chatInputContainer.style.display = 'none';
    searchInput.style.height = '40px'
    searchInput.value = ''
    thinkingNewDefault = false;
    updateThinkingUI(false);
  });

  // === Init ===
  updateSidebar();
});