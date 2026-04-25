import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import Home from '../pages/Home';
import Search from '../pages/Search';
import Chatbot from '../pages/Chatbot';
import Schedule from '../pages/Schedule';

const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* 모든 페이지에 공통 레이아웃(Header/Footer)을 적용합니다 */}
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />           {/* 홈 화면 */}
          <Route path="search" element={<Search />} />     {/* 여행 찾기 */}
          <Route path="chatbot" element={<Chatbot />} />   {/* 여행 챗봇 */}
          <Route path="schedule" element={<Schedule />} /> {/* 일정 만들기 */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default Router;