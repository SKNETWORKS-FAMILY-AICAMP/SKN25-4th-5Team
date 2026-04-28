import { useNavigate } from 'react-router-dom';
import './Home.css';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      {/* Hero Section */}
      <section className="hero fade-up">
        <h1>
          사용자 맞춤형 
          <span> 여행 추천 시스템</span>
        </h1>
        <p>
          당신의 시간과 여행 조건을 고려해<br />  
          가장 현실적이고 효율적인 여행을 추천합니다.<br />
          이제 계획부터 이동까지 한 번에 해결하세요.
        </p>
      </section>

      {/* CTA Button */}
      <div className="start-center">
        <div 
          className="start-btn"
          onClick={() => navigate('/search')}
        >
          지금 여행 계획 시작하기 →
        </div>
      </div>

      {/* Features Cards */}
      <section className="features-section">
        <div className="card">
          <h2>맞춤 추천</h2>
          <p>사용자 조건 기반 여행지 추천</p>
        </div>

        <div className="card">
          <h2>대화형 인터페이스</h2>
          <p>AI 챗봇으로 여행 관련 질문 실시간 응답</p>
        </div>

        <div className="card">
          <h2>빠른 추천</h2>
          <p>즉시 여행지 제공</p>
        </div>

        <div className="card">
          <h2>10000+</h2>
          <p>다양한 여행지 데이터</p>
        </div>
      </section>
    </div>
  );
}
