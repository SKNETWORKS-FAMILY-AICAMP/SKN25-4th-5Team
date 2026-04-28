import { Outlet, useLocation } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import view1 from '../../assets/view1.jpg';
import './Layout.css';

export default function Layout() {
  const location = useLocation();
  const isHomePage = location.pathname === '/';

  return (
    <div
      className={`layout ${isHomePage ? 'layout-home' : ''}`}
      style={isHomePage ? { '--layout-bg-image': `url(${view1})` } : undefined}
    >
      <Header />
      <main className="main-content">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
