import { useState } from 'react';
import './Search.css';

const destinations = [
  "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
  "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원특별자치도",
  "충청북도", "충청남도", "전북특별자치도", "전라남도", "경상북도",
  "경상남도", "제주특별자치도"
];

const purposes = [
  "관광지", "음식점", "숙박", "문화시설", "레포츠",
  "쇼핑", "축제/공연/행사"
];

const transportations = [
  "차량대여/렌트", "선박/해상 교통", "[정기] 고속/시외/시내버스",
  "자전거", "철도", "지하철", "도보", "택시", "항공기",
  "[부정기] 전세/관광버스", "자가용", "기타"
];

const companions = [
  "단독(혼자)", "친구", "연인", "배우자", "부모", "자녀",
  "형제/자매", "조부모", "손자/손녀", "직장동료",
  "학교 단체", "친목 단체/모임", "반려동물", "기타"
];

export default function Search() {
  const [destination, setDestination] = useState(destinations[0]);
  const [purpose, setPurpose] = useState(purposes[0]);
  const [transportation, setTransportation] = useState(transportations[0]);
  const [selectedCompanions, setSelectedCompanions] = useState([]);
  const [duration, setDuration] = useState(5);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleCompanionToggle = (companion) => {
    setSelectedCompanions(prev =>
      prev.includes(companion)
        ? prev.filter(c => c !== companion)
        : [...prev, companion]
    );
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/recommend/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            destination,
            purpose,
            transportation,
            companion: selectedCompanions.join(", "),
            duration
          })
        }
      );
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Search error:', error);
      alert('검색 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-container">
      <h1>맞춤형 여행지 추천</h1>
      <p className="subtitle">설정한 조건에 맞춰 최적의 여행 추천지를 보여줍니다.</p>
      <hr className="divider" />

      {/* Filters */}
      <div className="filters-section">
        <div className="filter-grid-2">
          <div className="filter-group">
            <label>목적지 선택</label>
            <select 
              value={destination} 
              onChange={(e) => setDestination(e.target.value)}
              className="select-input"
            >
              {destinations.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>여행 목적</label>
            <select 
              value={purpose} 
              onChange={(e) => setPurpose(e.target.value)}
              className="select-input"
            >
              {purposes.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="filter-grid-2">
          <div className="filter-group">
            <label>이동 수단</label>
            <select 
              value={transportation} 
              onChange={(e) => setTransportation(e.target.value)}
              className="select-input"
            >
              {transportations.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>동행자 유형</label>
            <div className="multiselect-container">
              {companions.map(companion => (
                <label key={companion} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={selectedCompanions.includes(companion)}
                    onChange={() => handleCompanionToggle(companion)}
                  />
                  {companion}
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="filter-grid-2">
          <div className="filter-group">
            <label>최대 이동 시간 (시간): {duration}시간</label>
            <input 
              type="range" 
              min="1" 
              max="24" 
              value={duration}
              onChange={(e) => setDuration(Number(e.target.value))}
              className="slider-input"
            />
          </div>

          <div className="filter-group button-group">
            <button 
              onClick={handleSearch}
              disabled={loading}
              className="search-btn"
            >
              {loading ? '검색 중...' : '🔍 검색'}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="results-section">
          <h2>검색 결과</h2>
          <div className="results-grid">
            {results.map((place, idx) => (
              <div key={idx} className="result-card">
                <h3>{place.title}</h3>
                <p className="location">{place.location}</p>
                <p className="content-type">{place.content_type}</p>
                <p className="description">{place.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {!loading && results.length === 0 && (
        <div className="empty-state">
          <p>조건을 선택하고 검색 버튼을 눌러주세요.</p>
        </div>
      )}
    </div>
  );
}
