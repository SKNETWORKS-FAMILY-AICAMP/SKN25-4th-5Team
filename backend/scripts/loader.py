"""
데이터 로더 - Docker 시작 시 자동으로 실행되어 pickle 파일을 PostgreSQL에 로드
"""

import os
import sys
import time
import psycopg2
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

BASE_DIR = Path(__file__).resolve().parent


def get_connection():
    """PostgreSQL 연결"""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        dbname=os.getenv("POSTGRES_DB"),
    )


def wait_for_db(max_retries=10, delay=2):
    """DB가 준비될 때까지 대기"""
    print("PostgreSQL 연결 대기 중...")
    
    for i in range(max_retries):
        try:
            conn = get_connection()
            conn.close()
            print("PostgreSQL 연결 성공")
            return True
        except Exception as e:
            print(f"시도 {i+1}/{max_retries} 실패: {str(e)[:50]}")
            time.sleep(delay)
    
    print("PostgreSQL 연결 실패")
    return False


def create_tables():
    """PostgreSQL 테이블 생성"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DROP TABLE IF EXISTS travel_places CASCADE;
                CREATE TABLE travel_places (
                    source VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content_type_nm VARCHAR(100),
                    sido_nm VARCHAR(50),
                    sgg_nm VARCHAR(50),
                    zipcode VARCHAR(20),
                    latitude FLOAT,
                    longitude FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            cur.execute("""
                DROP TABLE IF EXISTS user_behavior CASCADE;
                CREATE TABLE user_behavior (
                    with_pet VARCHAR(5),
                    gender VARCHAR(20),
                    age_group VARCHAR(20),
                    trip_visit_area VARCHAR(20),
                    trip_stay_area VARCHAR(20),
                    trip_stay_type VARCHAR(100),
                    trip_transport_city2city VARCHAR(50),
                    trip_transport_incity VARCHAR(50),
                    trip_transport_incity2 VARCHAR(50),
                    companion_type VARCHAR(100),
                    travel_activity VARCHAR(100),
                    trip_visit_sido VARCHAR(50),
                    trip_visit_sigungu VARCHAR(50),
                    trip_stay_sido VARCHAR(50),
                    trip_stay_sigungu VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        conn.commit()
        print("테이블 생성 완료")
        return True
    except Exception as e:
        print(f"테이블 생성 실패: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def load_pickle_data():
    """Pickle 파일을 DB에 로드"""
    data_dir = BASE_DIR.parent / "db" / "processed"
    
    print("Pickle 파일 로드 중...")
    
    try:
        df_regional = pd.read_pickle(data_dir / "tourpoi.pkl")
        df_barrier_free = pd.read_pickle(data_dir / "barrier_free.pkl")
        df_pet = pd.read_pickle(data_dir / "pet_df_final.pkl")
        df_behavior = pd.read_pickle(data_dir / "tour_survey_final.pkl")
        
        print(f"관광지: {len(df_regional)} 행")
        print(f"무장애 여행지: {len(df_barrier_free)} 행")
        print(f"반려동물 여행지: {len(df_pet)} 행")
        print(f"행동 패턴: {len(df_behavior)} 행")
    except Exception as e:
        print(f"파일 로드 실패: {e}")
        return False
    
    print("데이터 정제 중...")
    
    for col in df_behavior.columns:
        if df_behavior[col].dtype == 'object':
            df_behavior[col] = df_behavior[col].fillna('N')
        else:
            df_behavior[col] = df_behavior[col].fillna('N')
    
    print("DB에 저장 중...")
    conn = get_connection()
    
    saved_count = 0
    
    try:
        for source_name, df, columns in [
            ('regional', df_regional, ['title', 'content_type_nm', 'sido_nm', 'sgg_nm', 'longitude', 'latitude']),
            ('barrier_free', df_barrier_free, ['title', 'content_type_nm', 'sido_nm', 'sgg_nm', 'longitude', 'latitude', 'zipcode']),
            ('pet', df_pet, ['title', 'content_type_nm', 'sido_nm', 'sgg_nm', 'longitude', 'latitude', 'zipcode'])
        ]:
            count = 0
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    try:
                        if source_name in ['barrier_free', 'pet']:
                            cur.execute("""
                                INSERT INTO travel_places (
                                    source, title, content_type_nm, sido_nm, 
                                    sgg_nm, zipcode, latitude, longitude
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                source_name,
                                str(row.get('title', 'Unknown'))[:255],
                                str(row.get('content_type_nm', ''))[:100] if pd.notna(row.get('content_type_nm')) else None,
                                str(row.get('sido_nm', ''))[:50] if pd.notna(row.get('sido_nm')) else None,
                                str(row.get('sgg_nm', ''))[:50] if pd.notna(row.get('sgg_nm')) else None,
                                str(row.get('zipcode', ''))[:20] if pd.notna(row.get('zipcode')) else None,
                                float(row.get('latitude')) if pd.notna(row.get('latitude')) else None,
                                float(row.get('longitude')) if pd.notna(row.get('longitude')) else None,
                            ))
                        else:
                            cur.execute("""
                                INSERT INTO travel_places (
                                    source, title, content_type_nm, sido_nm, 
                                    sgg_nm, latitude, longitude
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (
                                source_name,
                                str(row.get('title', 'Unknown'))[:255],
                                str(row.get('content_type_nm', ''))[:100] if pd.notna(row.get('content_type_nm')) else None,
                                str(row.get('sido_nm', ''))[:50] if pd.notna(row.get('sido_nm')) else None,
                                str(row.get('sgg_nm', ''))[:50] if pd.notna(row.get('sgg_nm')) else None,
                                float(row.get('latitude')) if pd.notna(row.get('latitude')) else None,
                                float(row.get('longitude')) if pd.notna(row.get('longitude')) else None,
                            ))
                        count += 1
                        saved_count += 1
                    except Exception as row_err:
                        pass
            
            conn.commit()
            print(f"{source_name} 로드 완료 ({count}개)")
        
        count = 0
        with conn.cursor() as cur:
            for _, row in df_behavior.iterrows():
                try:
                    cur.execute("""
                        INSERT INTO user_behavior (
                            with_pet, gender, age_group, trip_visit_area,
                            trip_stay_area, trip_stay_type, trip_transport_city2city,
                            trip_transport_incity, trip_transport_incity2, companion_type,
                            travel_activity, trip_visit_sido, trip_visit_sigungu,
                            trip_stay_sido, trip_stay_sigungu
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(row.get('with_pet', 'N'))[:5],
                        str(row.get('gender', 'N'))[:20],
                        str(row.get('age_group', 'N'))[:20],
                        str(row.get('trip_visit_area', 'N'))[:20],
                        str(row.get('trip_stay_area', 'N'))[:20],
                        str(row.get('trip_stay_type', 'N'))[:100],
                        str(row.get('trip_transport(city2city)', 'N'))[:50],
                        str(row.get('trip_transport(incity)', 'N'))[:50],
                        str(row.get('trip_transport(incity)2', 'N'))[:50],
                        str(row.get('companion_type', 'N'))[:100],
                        str(row.get('travel_activity', 'N'))[:100],
                        str(row.get('trip_visit_sido', 'N'))[:50],
                        str(row.get('trip_visit_sigungu', 'N'))[:50],
                        str(row.get('trip_stay_sido', 'N'))[:50],
                        str(row.get('trip_stay_sigungu', 'N'))[:50],
                    ))
                    count += 1
                    saved_count += 1
                except Exception as row_err:
                    pass
        
        conn.commit()
        print(f"행동 패턴 로드 완료 ({count}개)")
        
        print(f"총 {saved_count}개 레코드 저장 완료")
        return True
    except Exception as e:
        print(f"데이터 삽입 실패: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def main():
    """데이터 로더 메인 함수"""
    print("데이터 로더 시작")
    
    if not wait_for_db():
        print("DB 연결 실패로 로더 종료")
        sys.exit(1)
    
    print("테이블 생성 중...")
    if not create_tables():
        print("테이블 생성 실패로 로더 종료")
        sys.exit(1)
    
    print("데이터 로드 중...")
    if not load_pickle_data():
        print("데이터 로드 실패로 로더 종료")
        sys.exit(1)
    
    print("모든 작업 완료. Backend 서버 준비 완료")


if __name__ == "__main__":
    main()
