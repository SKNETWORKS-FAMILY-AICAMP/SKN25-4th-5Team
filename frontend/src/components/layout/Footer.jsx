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
          
          <div className="footer-section">
            <h4>빠른 링크</h4>
            <ul>
              <li><a href="/">홈</a></li>
              <li><a href="/search">여행 찾기</a></li>
              <li><a href="/chat">챗봇</a></li>
              <li><a href="/schedule">일정 만들기</a></li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>연락처</h4>
            <p>Email: info@tripick.com</p>
            <p>Phone: 010-0000-0000</p>
          </div>
        </div>

        <div className="footer-bottom">
          <p>&copy; 2026 Tripick. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
