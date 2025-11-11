(() => {
  const dom = {
    endpointInput: document.getElementById('endpoint-input'),
    saveEndpointBtn: document.getElementById('save-endpoint-btn'),
    userIdEl: document.getElementById('user-id'),
    messages: document.getElementById('messages'),
    form: document.getElementById('chat-form'),
    questionInput: document.getElementById('question-input'),
    sendBtn: document.getElementById('send-btn')
  };

  // 简单的 UUID 生成（页面级即可）
  function generateUserId() {
    const base = Math.random().toString(36).slice(2, 10);
    const time = Date.now().toString(36);
    return `user_${time}_${base}`;
  }

  // 每个浏览器标签页独立的 user_id，存在 sessionStorage
  const USER_ID_KEY = 'qa_user_id';
  function getOrCreateUserId() {
    let id = sessionStorage.getItem(USER_ID_KEY);
    if (!id) {
      id = generateUserId();
      sessionStorage.setItem(USER_ID_KEY, id);
    }
    return id;
  }

  // 后端地址配置，存在 localStorage（跨会话记忆）
  const ENDPOINT_KEY = 'qa_endpoint';
  function getEndpoint() {
    return localStorage.getItem(ENDPOINT_KEY) || '';
  }
  function setEndpoint(url) {
    localStorage.setItem(ENDPOINT_KEY, url.trim());
  }

  function scrollToBottom() {
    dom.messages.scrollTop = dom.messages.scrollHeight;
  }

  function appendMessage(role, text) {
    const wrapper = document.createElement('div');
    wrapper.className = `msg ${role}`;
    const roleEl = document.createElement('div');
    roleEl.className = 'role';
    roleEl.textContent = role === 'user' ? '你' : (role === 'assistant' ? '回答' : '');
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    wrapper.appendChild(roleEl);
    wrapper.appendChild(bubble);
    dom.messages.appendChild(wrapper);
    scrollToBottom();
  }

  function appendError(text) {
    const wrapper = document.createElement('div');
    wrapper.className = 'msg error';
    const roleEl = document.createElement('div');
    roleEl.className = 'role';
    roleEl.textContent = '错误';
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    wrapper.appendChild(roleEl);
    wrapper.appendChild(bubble);
    dom.messages.appendChild(wrapper);
    scrollToBottom();
  }

  async function callBackend(question) {
    const endpoint = getEndpoint();
    if (!endpoint) {
      throw new Error('请先在顶部输入并保存后端地址');
    }
    const userId = getOrCreateUserId();
    const payload = {
      user_id: userId,
      user_question: question,
      stream: false
    };

    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!resp.ok) {
      const text = await resp.text().catch(() => '');
      throw new Error(`请求失败：${resp.status} ${resp.statusText} ${text}`.trim());
    }

    // 兼容返回 JSON: { ... }
    const data = await resp.json();
    // 适配后端 BaseResponse: { code, message, data, product_list }
    if (data && typeof data === 'object' && 'code' in data) {
      if (Number(data.code) !== 200) {
        throw new Error(data.message || '后端返回错误');
      }
    }
    return data;
  }

  function formatAnswer(data) {
    // 适配常见返回：强制优先 BaseResponse.data（为字符串的完整回答）
    if (!data || typeof data !== 'object') return String(data);
    if ('code' in data && Number(data.code) === 200) {
      if (typeof data.data === 'string' && data.data.trim() !== '') return data.data;
    }
    if (typeof data.data === 'string') return data.data;
    if (typeof data.answer === 'string') return data.answer;
    if (data.data && typeof data.data.answer === 'string') return data.data.answer;
    if (typeof data.message === 'string') return data.message;
    // 兜底串行化
    return JSON.stringify(data, null, 2);
  }

  function setLoading(loading) {
    dom.sendBtn.disabled = loading;
    dom.sendBtn.textContent = loading ? '发送中…' : '发送';
  }

  // 事件绑定与初始化
  function init() {
    const userId = getOrCreateUserId();
    dom.userIdEl.textContent = userId;

    const saved = getEndpoint();
    if (saved) dom.endpointInput.value = saved;

    dom.saveEndpointBtn.addEventListener('click', () => {
      const value = dom.endpointInput.value.trim();
      if (!value) {
        alert('后端地址不能为空');
        return;
      }
      setEndpoint(value);
      alert('已保存');
    });

    dom.form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = dom.questionInput.value.trim();
      if (!question) return;

      appendMessage('user', question);
      dom.questionInput.value = '';
      setLoading(true);
      try {
        const data = await callBackend(question);
        const answerText = formatAnswer(data);
        appendMessage('assistant', answerText);
      } catch (err) {
        appendError(err.message || String(err));
      } finally {
        setLoading(false);
      }
    });
  }

  init();
})();


