import { Outlet } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';

const Layout = () => {
  return (
    <div className="layout-wrapper">
      <Header /> {/* 상단 고정 */}
      
      <main className="main-content">
        {/* Router에서 설정한 자식 Route들이 이 자리에 렌더링됩니다 */}
        <Outlet /> 
      </main>

      <Footer /> {/* 하단 고정 */}
    </div>
  );
};

export default Layout;