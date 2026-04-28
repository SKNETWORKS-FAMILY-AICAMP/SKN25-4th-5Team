import { useState } from 'react';
import './Schedule.css';

const destinations = [
  "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시",
  "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원특별자치도",
  "충청북도", "충청남도", "전북특별자치도", "전라남도", "경상북도",
  "경상남도", "제주특별자치도"
];

const travelTypes = [
  "가족/친지 방문", "교육/체험 프로그램", "교육/훈련/연수",
  "드라마 촬영지 방문", "문화예술/전시 관람", "스포츠 경기관람",
  "시티투어", "야외 스포츠/레포츠", "역사 유적지 방문",
  "온천/스파", "유흥/오락", "자연 및 풍경감상",
  "종교/성지순례", "지역 축제/이벤트", "카지노/경마 등",
  "테마파크/동식물원", "회의참가/시찰", "휴식/휴양",
  "쇼핑", "음식관광", "기타"
];

const transportations = [
  "차량대여/렌트", "선박/해상 교통", "[정기] 고속/시외/시내버스",
  "자전거", "철도", "지하철", "도보", "택시", "항공기",
  "[부정기] 전세/관광버스", "자가용", "기타"
];

export default function Schedule() {
  const [departure, setDeparture] = useState(destinations[0]);
  const [destination, setDestination] = useState(destinations[1]);
  const [travelType, setTravelType] = useState(travelTypes[0]);
  const [transportation, setTransportation] = useState(transportations[0]);
  const [departureHour, setDepartureHour] = useState(9);
  const [dayCount, setDayCount] = useState(1);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleMakePlan = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/plan`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            departure,
            destination,
            travel_type: travelType,
            transportation,
            departure_hour: departureHour,
            day_count: dayCount
          })
        }
      );
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Plan error:', error);
      alert('일정 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatHour = (hour) => {
    const period = hour >= 12 ? '오후' : '오전';
    const displayHour = hour > 12 ? hour - 12 : hour === 0 ? 12 : hour;
    return `${period} ${displayHour}:00`;
  };

  return (
    <div className="schedule-container">
      <h1>여행 플래너</h1>
      <p className="subtitle">설정한 조건에 맞춰 최적의 여행 경로를 설계합니다.</p>
      <hr className="divider" />

      {/* Plan Configuration */}
      <div className="plan-section">
        <div className="form-grid-2">
          <div className="form-group">
            <label>출발지 선택</label>
            <select 
              value={departure}
              onChange={(e) => setDeparture(e.target.value)}
              className="select-input"
            >
              {destinations.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>도착지 선택</label>
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
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label>여행 유형</label>
            <select 
              value={travelType}
              onChange={(e) => setTravelType(e.target.value)}
              className="select-input"
            >
              {travelTypes.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
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
        </div>

        <div className="form-grid-2">
          <div className="form-group">
            <label>출발 시간: {formatHour(departureHour)}</label>
            <input 
              type="range"
              min="0"
              max="24"
              value={departureHour}
              onChange={(e) => setDepartureHour(Number(e.target.value))}
              className="slider-input"
              style={{
                '--slider-progress': `${(departureHour / 24) * 100}%`
              }}
            />
          </div>

          <div className="form-group">
            <label>여행 기간: {dayCount}일</label>
            <input 
              type="range"
              min="1"
              max="14"
              value={dayCount}
              onChange={(e) => setDayCount(Number(e.target.value))}
              className="slider-input"
              style={{
                '--slider-progress': `${((dayCount - 1) / (14 - 1)) * 100}%`
              }}
            />
          </div>
        </div>

        <div className="button-container">
          <button 
            onClick={handleMakePlan}
            disabled={loading}
            className="plan-btn"
          >
            {loading ? '일정 생성 중...' : '✈️ 여행 일정 생성'}
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className="result-container">
          <h2>Tripick 추천 일정</h2>
          
          <div className="trip-info">
            <div className="info-item">
              <span className="label">출발지</span>
              <span className="value">{result.departure}</span>
            </div>
            <div className="info-item">
              <span className="label">도착지</span>
              <span className="value">{result.destination}</span>
            </div>
            <div className="info-item">
              <span className="label">여행 기간</span>
              <span className="value">{result.day_count}일</span>
            </div>
          </div>

          {result.itinerary && result.itinerary.length > 0 && (
            <div className="itinerary-section">
              <h3>상세 일정</h3>
              {result.itinerary.map((day, idx) => (
                <div key={idx} className="day-plan">
                  <h4>DAY {idx + 1}</h4>
                  <div className="activities">
                    {day.activities && day.activities.map((activity, i) => (
                      <div key={i} className="activity-item">
                        <span className="time">{activity.time || '시간 미정'}</span>
                        <span className="activity">{activity.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {result.recommendations && result.recommendations.length > 0 && (
            <div className="recommendations-section">
              <h3>추천 장소</h3>
              <div className="places-grid">
                {result.recommendations.map((place, idx) => (
                  <div key={idx} className="place-card">
                    <h4>{place.title}</h4>
                    <p className="location">{place.location}</p>
                    {place.description && (
                      <p className="description">{place.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <button onClick={() => setResult(null)} className="reset-btn">
            다른 일정 생성하기
          </button>
        </div>
      )}

      {!loading && !result && (
        <div className="empty-state">
          <p>조건을 선택하고 여행 일정을 생성하세요.</p>
        </div>
      )}
    </div>
  );
}
