import { useNavigate } from 'react-router-dom';
import logo from '../../assets/logo.png';
import './Header.css';

export default function Header() {
  const navigate = useNavigate();

  return (
    <header className="header">
      <div className="header-container">
        <div className="logo">
          <img 
            src={logo} 
            alt="Tripick" 
            onClick={() => navigate('/')}
            className="logo-img"
          />
        </div>
        
        <nav className="nav-menu">
          <button 
            className="nav-btn"
            onClick={() => navigate('/search')}
          >
            여행 찾기
          </button>
          <button 
            className="nav-btn"
            onClick={() => navigate('/chat')}
          >
            여행 챗봇
          </button>
          <button 
            className="nav-btn"
            onClick={() => navigate('/schedule')}
          >
            일정 만들기
          </button>
          <button 
            className="nav-btn"
            onClick={() => navigate('/')}
          >
            서비스 소개
          </button>
        </nav>
      </div>
    </header>
  );
}
