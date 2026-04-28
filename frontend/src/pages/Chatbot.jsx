import { useState, useEffect, useRef, useCallback } from 'react';
import './Chatbot.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: `안녕하세요 😊

**맞춤 여행 추천 챗봇**이에요!
우리 DB의 실제 관광 데이터를 바탕으로 답변해 드립니다.

어떤 여행을 계획하고 계신가요?
예를 들어 이렇게 말해주시면 좋아요:

- "서울에서 2시간 내로 갈 수 있는 데이트 코스 추천해줘"
- "반려동물과 함께 갈 수 있는 강릉 카페 알려줘"
- "휠체어로 이용 가능한 제주도 관광지 추천해줘"

조건을 알려주시면 딱 맞게 추천해드릴게요 ✈️`
};

export default function Chatbot() {
  const [chatId, setChatId] = useState(null);
  const [chatList, setChatList] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const chatWindowRef = useRef(null);
  const scrollFrameRef = useRef(null);
  const skipNextAutoScrollRef = useRef(false);

  const scrollToBottom = useCallback((behavior = 'smooth') => {
    if (scrollFrameRef.current) {
      cancelAnimationFrame(scrollFrameRef.current);
    }

    scrollFrameRef.current = requestAnimationFrame(() => {
      if (!chatWindowRef.current) return;

      chatWindowRef.current.scrollTo({
        top: chatWindowRef.current.scrollHeight,
        behavior
      });
    });
  }, []);

  useEffect(() => {
    if (skipNextAutoScrollRef.current) {
      skipNextAutoScrollRef.current = false;
      requestAnimationFrame(() => {
        chatWindowRef.current?.scrollTo({ top: 0 });
      });
      return;
    }

    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (scrollFrameRef.current) {
        cancelAnimationFrame(scrollFrameRef.current);
      }
    };
  }, []);

  const fetchChatList = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/list/`);
      if (!response.ok) throw new Error('Failed to load chat list');
      const data = await response.json();
      setChatList(data);
    } catch (error) {
      console.error('Chat list error:', error);
    }
  }, []);

  useEffect(() => {
    fetchChatList();
  }, [fetchChatList]);

  const createChat = async (message) => {
    const response = await fetch(`${API_BASE_URL}/api/chat/create/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });

    if (!response.ok) throw new Error('Failed to create chat');

    const data = await response.json();
    setChatId(data.chat_id);
    return data.chat_id;
  };

  const saveMessage = async (targetChatId, message) => {
    const response = await fetch(`${API_BASE_URL}/api/chat/save/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: targetChatId,
        role: message.role,
        content: message.content,
        places: message.places || []
      })
    });

    if (!response.ok) throw new Error('Failed to save message');
  };

  const handleNewChat = () => {
    setChatId(null);
    setMessages([INITIAL_MESSAGE]);
    setInputValue('');
  };

  const handleLoadChat = async (selectedChatId) => {
    setHistoryLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/${selectedChatId}/`);
      if (!response.ok) throw new Error('Failed to load chat');

      const data = await response.json();
      setChatId(selectedChatId);
      skipNextAutoScrollRef.current = true;
      setMessages(data.length > 0 ? data : [INITIAL_MESSAGE]);
    } catch (error) {
      console.error('Load chat error:', error);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();

    if (!inputValue.trim()) return;

    const currentInput = inputValue.trim();
    const userMessage = { role: 'user', content: currentInput };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const activeChatId = chatId || await createChat(currentInput);
      await saveMessage(activeChatId, userMessage);

      // Prepare history (last 6 messages excluding the new one)
      const history = messages.slice(-6).map(msg => ({
        role: msg.role,
        content: msg.content,
        ...(msg.places && { places: msg.places.slice(0, 5) })
      }));

      const response = await fetch(
        `${API_BASE_URL}/api/chat/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: currentInput,
            history,
            limit: 5
          })
        }
      );

      if (!response.ok) throw new Error('API request failed');

      const data = await response.json();
      const assistantMessage = {
        role: 'assistant',
        content: data.answer || '답변을 가져오지 못했습니다.',
        places: data.places || []
      };

      setMessages(prev => [...prev, assistantMessage]);
      await saveMessage(activeChatId, assistantMessage);
      await fetchChatList();
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: '서버에 연결할 수 없습니다. 다시 시도해주세요.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div>
          <h1>여행 챗봇</h1>
          <p>대화를 바탕으로 여행지 추천과 후속 계획을 도와줍니다.</p>
        </div>
      </div>

      <div className="chatbot-layout">
        <button
          type="button"
          className="history-toggle"
          onClick={() => setSidebarOpen(prev => !prev)}
          aria-label={sidebarOpen ? '대화 기록 닫기' : '대화 기록 열기'}
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <aside className={`chat-history ${sidebarOpen ? 'open' : ''}`}>
          <div className="history-header">
            <h2>대화 기록</h2>
            <button type="button" className="new-chat-btn" onClick={handleNewChat}>
              새 대화
            </button>
          </div>

          <div className="history-list">
            {chatList.length === 0 && (
              <p className="history-empty">저장된 대화가 없습니다.</p>
            )}

            {chatList.map(chat => (
              <button
                type="button"
                key={chat.id}
                className={`history-item ${chatId === chat.id ? 'active' : ''}`}
                onClick={() => handleLoadChat(chat.id)}
                disabled={historyLoading}
              >
                <span>{chat.title || '새 대화'}</span>
              </button>
            ))}
          </div>
        </aside>

        <div className="chat-main">
          <div className="chat-window" ref={chatWindowRef}>
            <div className="messages">
              {messages.map((message, idx) => (
                <div key={idx} className={`message-wrapper ${message.role}`}>
                  <div className="message">
                    <div className="message-content">
                      {/* Simple markdown-like parsing */}
                      {message.content.split('\n').map((line, i) => {
                        if (line.startsWith('**') && line.endsWith('**')) {
                          return <strong key={i}>{line.replace(/\*\*/g, '')}</strong>;
                        }
                        if (line.startsWith('- ')) {
                          return <li key={i}>{line.substring(2)}</li>;
                        }
                        return <p key={i}>{line}</p>;
                      })}
                    </div>

                    {message.places && message.places.length > 0 && (
                      <div className="places-list">
                        <h4>추천 장소:</h4>
                        {message.places.map((place, i) => (
                          <div key={i} className="place-item">
                            <strong>{place.title}</strong>
                            <p>{place.location || [place.sido_nm, place.sgg_nm].filter(Boolean).join(' ')}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message-wrapper assistant">
                  <div className="message loading">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <p className="loading-text">최적의 여행 데이터를 검색 중입니다...</p>
                  </div>
                </div>
              )}

            </div>
          </div>

          <form className="chat-input-form" onSubmit={handleSendMessage}>
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="메시지를 입력해주세요."
              className="chat-input"
              disabled={loading}
            />
            <button
              type="submit"
              className="send-btn"
              disabled={loading || !inputValue.trim()}
            >
              전송
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}