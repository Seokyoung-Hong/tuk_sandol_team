from typing import Optional
import pandas as pd

# ClassRoom 클래스 정의
class ClassRoom:
    """강의실 정보를 나타내는 클래스.

    Attributes:
        building (str): 강의실이 위치한 건물 이름.
        room (int | str): 강의실 번호.
        day (str): 강의실이 비는 요일.
        free_from (int): 강의실이 비는 시작 시간 (예: 930은 09:30).
        free_to (int): 강의실이 비는 종료 시간 (예: 2200은 22:00).
    """
    
    def __init__(self, building: str, room: int | str, day: str, free_from: int, free_to: int):
        """
        Args:
            building (str): 강의실이 위치한 건물 이름.
            room (int | str): 강의실 번호.
            day (str): 강의실이 비는 요일.
            free_from (int): 강의실이 비는 시작 시간 (예: 930은 09:30).
            free_to (int): 강의실이 비는 종료 시간 (예: 2200은 22:00).
        """
        self.building = building
        self.room = room
        self.day = day
        self.free_from = free_from
        self.free_to = free_to

    def __repr__(self):
        """강의실 정보를 문자열로 반환."""
        return f"ClassRoom(building='{self.building}', room='{self.room}', day='{self.day}', free_from={self.free_from}, free_to={self.free_to})"


# EmptyRoomSchedule 클래스로 관리
class EmptyRoomSchedule:
    """강의실 빈 시간표를 관리하는 클래스.

    이 클래스는 CSV 파일로부터 강의실의 빈 시간 정보를 로드하고, 필터링 및 복원 기능을 제공합니다.

    Attributes:
        df (pd.DataFrame): 강의실 데이터가 저장된 DataFrame.
        _original (pd.DataFrame): 초기 강의실 데이터 (복원용).
    """

    def __init__(self, path: str = "./sandol/crawler/source/empty_rooms_schedule.csv"):
        """EmptyRoomSchedule 클래스의 초기화 함수.

        CSV 파일을 로드하고, 원본 데이터를 저장합니다.

        Args:
            path (str): 강의실 시간표 파일의 경로 (기본값은 './sandol/crawler/source/empty_rooms_schedule.csv').
        """
        self.df = self.load_classroom_file(path)
        self._original = self.df.copy()

    def load_classroom_file(self, path: str) -> pd.DataFrame:
        """CSV 파일로부터 강의실 데이터를 로드하는 함수.

        Args:
            path (str): CSV 파일 경로.

        Returns:
            pd.DataFrame: 로드된 강의실 시간표 데이터.
        """
        df = pd.read_csv(path)
        return df

    def df_to_ClassRoom_list(self) -> list[ClassRoom]:
        """DataFrame 데이터를 ClassRoom 객체 리스트로 변환하는 함수.

        Returns:
            list[ClassRoom]: ClassRoom 객체 리스트.
        """
        result = []
        for _, row in self.df.iterrows():
            classroom = ClassRoom(
                building=row['Building'],
                room=row['Room Number'],
                day=row['Day'],
                free_from=row['Free From'],
                free_to=row['Free To']
            )
            result.append(classroom)
        return result

    def filter_classrooms(self, day: str, from_time: int, to_time: int, building: Optional[str] = None) -> pd.DataFrame:
        """입력받은 조건에 맞는 강의실을 필터링하는 함수.

        Args:
            day (str): 필터링할 요일 (예: '월', '화').
            from_time (int): 시작 시간 (예: 930은 09:30).
            to_time (int): 종료 시간 (예: 1800은 18:00).
            building (Optional[str]): 특정 건물 이름 (지정하지 않으면 건물 필터링을 하지 않음).

        Returns:
            pd.DataFrame: 필터링된 강의실 정보를 포함한 DataFrame.
        """
        condition = (
            (self.df['Day'] == day) & 
            (self.df['Free From'] <= from_time) & 
            (self.df['Free To'] >= to_time)
        )

        if building:
            condition = condition & (self.df['Building'] == building)

        self.df = self.df[condition]
        return self.df

    def restore_classrooms(self) -> pd.DataFrame:
        """필터링된 강의실 정보를 원래 상태로 복원하는 함수.

        Returns:
            pd.DataFrame: 복원된 원본 강의실 데이터.
        """
        self.df = self._original.copy()
        return self.df


if __name__ == "__main__":
    """모듈을 직접 실행할 때의 예시 코드."""
    schedule = EmptyRoomSchedule()  # 객체 생성 시 자동으로 파일을 로드함
    filtered_df = schedule.filter_classrooms('월', 930, 2200, building='B동')  # B동, '월' 요일, 09:30~22:00 범위로 필터링
    classroom_list = schedule.df_to_ClassRoom_list()  # ClassRoom 리스트 변환
    print(filtered_df)
    print(classroom_list)
