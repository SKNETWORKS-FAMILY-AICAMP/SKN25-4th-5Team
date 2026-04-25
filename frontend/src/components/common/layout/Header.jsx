import { Link } from 'react-router-dom';
import './Header.css'; // 필요 시 스타일 적용

const Header = () => {
  return (
    <header className="header">
      <div className="logo-section">
        <Link to="/">
          <img src="/assets/logo.png" alt="Tripick 로고" />
        </Link>
      </div>
      <nav className="nav-menu">
        <Link to="/search">여행 찾기</Link>
        <Link to="/chatbot">여행 챗봇</Link>
        <Link to="/schedule">일정 만들기</Link>
        <Link to="/intro">서비스 소개</Link>
      </nav>
    </header>
  );
};

export default Header;