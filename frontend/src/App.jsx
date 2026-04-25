import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [msg, setMsg] = useState("로딩 중...");

  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL ?? "";

    fetch(`${apiUrl}/api/hello/`)
      .then((res) => res.json())
      .then((data) => setMsg(data.message))
      .catch((err) => {
        console.error(err);
        setMsg("API 연결 실패");
      });
  }, []);

  return (
    <div>
      <h1>React 화면 정상</h1>
      <h2>{msg}</h2>
    </div>
  );
}

export default App;
