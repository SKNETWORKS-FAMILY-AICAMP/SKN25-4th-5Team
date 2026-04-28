import { Routes, Route } from 'react-router-dom'; 
import Layout from '../components/layout/Layout';
import Home from '../pages/Home';
import Search from '../pages/Search';
import Chatbot from '../pages/Chatbot';
import Schedule from '../pages/Schedule';

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/chat" element={<Chatbot />} />
        <Route path="/schedule" element={<Schedule />} />
      </Route>
    </Routes>
  );
}