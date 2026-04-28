import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <h3>Tripick</h3>
            <p>사용자 맞춤형 여행 추천 시스템</p>
          </div>
          
          <nav className="footer-links" aria-label="푸터 메뉴">
            <a href="/">홈</a>
            <a href="/search">여행 찾기</a>
            <a href="/chat">챗봇</a>
            <a href="/schedule">일정 만들기</a>
          </nav>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 Tripick. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
