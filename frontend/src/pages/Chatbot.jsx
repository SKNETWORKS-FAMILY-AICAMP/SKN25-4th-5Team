import { useState, useEffect, useRef } from 'react';
import './Chatbot.css';

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
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = { role: 'user', content: inputValue };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      // Prepare history (last 6 messages excluding the new one)
      const history = messages.slice(-6).map(msg => ({
        role: msg.role,
        content: msg.content,
        ...(msg.places && { places: msg.places.slice(0, 5) })
      }));

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/chat/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: inputValue,
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
        <h1>여행 챗봇</h1>
        <p>대화를 바탕으로 여행지 추천과 후속 계획을 도와줍니다.</p>
      </div>

      <div className="chat-window">
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
                        <p>{place.location}</p>
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

          <div ref={messagesEndRef} />
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
  );
}
