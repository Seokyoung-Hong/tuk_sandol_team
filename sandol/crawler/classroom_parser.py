import pandas as pd
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

class LectureParser:
    def __init__(self, file_path: str):
        self.df = pd.read_excel(file_path)
        self.df = self.df.dropna(subset=['강의시간'])

    def parse_lecture_time(self, lecture_time: str) -> List[Dict[str, Any]]:
        time_pattern = r'(?P<day>\w+)\s*\[(?P<start_end>\d+~?\d*)\]\s*(?P<start_time>\d{2}:\d{2})~(?P<end_time>\d{2}:\d{2})'
        room_pattern = r'\((?P<room>.+)\)$'
        time_matches = re.finditer(time_pattern, lecture_time)
        result = []
        for match in time_matches:
            result.append({
                "day": match.group('day'),
                "start_time": match.group('start_time'),
                "end_time": match.group('end_time'),
                "room": None
            })
        room_match = re.search(room_pattern, lecture_time)
        if room_match:
            room_info = room_match.group('room')
            if any(keyword in room_info for keyword in ["온라인", "미배정", "연구실"]):
                return []
            room_list = room_info.split(',')
            for entry in result:
                entry['room_a'] = room_list[0].strip() if len(room_list) > 0 else None
                entry['room_b'] = room_list[1].strip() if len(room_list) > 1 else None
                if len(room_list) > 2:
                    raise ValueError("room is more than 2")
        return result

    def expand_lecture_times(self) -> pd.DataFrame:
        expanded_rows = []
        for _, row in self.df.iterrows():
            parsed_times = self.parse_lecture_time(row['강의시간'])
            for parsed_time in parsed_times:
                new_row = row.copy()
                new_row['Day'] = parsed_time['day']
                new_row['Free From'] = parsed_time['start_time']
                new_row['Free To'] = parsed_time['end_time']
                new_row['RoomA'] = parsed_time['room_a']
                new_row['RoomB'] = parsed_time['room_b']
                expanded_rows.append(new_row)
        return pd.DataFrame(expanded_rows)


class RoomScheduler:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.buildings = ['A동', 'B동', 'C동', 'D동', 'E동', 'F동', 'G동', '종합', 'TIP', '산융', '비즈']
        self.days = ['월', '화', '수', '목', '금', '토']
        self.room_schedule = {}

    def extract_room_schedule(self):
        for idx, row in self.df.iterrows():
            for room_col in ['RoomA', 'RoomB']:
                room = row.get(room_col)
                if pd.isna(room):
                    continue
                for single_room in room.split(','):
                    single_room = single_room.strip()
                    building = next((b for b in self.buildings if single_room.startswith(b)), None)
                    if not building:
                        continue
                    room_number = single_room.replace(building, '').strip()
                    if building not in self.room_schedule:
                        self.room_schedule[building] = {}
                    if room_number not in self.room_schedule[building]:
                        self.room_schedule[building][room_number] = {}
                    day = row['Day']
                    if day not in self.room_schedule[building][room_number]:
                        self.room_schedule[building][room_number][day] = []
                    start_time = row['Free From']
                    end_time = row['Free To']
                    try:
                        start_dt = datetime.strptime(start_time, '%H:%M')
                        end_dt = datetime.strptime(end_time, '%H:%M')
                    except ValueError:
                        print(f"시간 형식 오류: {start_time} ~ {end_time} in row {idx}")
                        continue
                    self.room_schedule[building][room_number][day].append((start_dt, end_dt))

    def find_empty_rooms(self) -> pd.DataFrame:
        self.extract_room_schedule()
        operating_start = datetime.strptime('09:30', '%H:%M')
        operating_end = datetime.strptime('22:00', '%H:%M')
        min_free_duration = timedelta(minutes=30)
        empty_rooms = []

        for building, rooms in self.room_schedule.items():
            for room_number, schedule in rooms.items():
                for day in self.days:
                    booked_times = schedule.get(day, [])
                    booked_times.sort(key=lambda x: x[0])
                    if not booked_times:
                        free_times = [(operating_start, operating_end)]
                    else:
                        free_times = []
                        current_time = operating_start
                        for start, end in booked_times:
                            if current_time < start:
                                free_start = current_time
                                free_end = start
                                duration = free_end - free_start
                                if duration >= min_free_duration:
                                    free_times.append((free_start, free_end))
                            current_time = max(current_time, end)
                        if current_time < operating_end:
                            free_start = current_time
                            free_end = operating_end
                            duration = free_end - free_start
                            if duration >= min_free_duration:
                                free_times.append((free_start, free_end))
                    for free_start, free_end in free_times:
                        empty_rooms.append({
                            'Building': building,
                            'Room Number': room_number,
                            'Day': day,
                            'Free From': free_start.strftime('%H%M'),
                            'Free To': free_end.strftime('%H%M')
                        })

        return pd.DataFrame(empty_rooms)

    def save_empty_rooms_to_csv(self, output_file: str):
        empty_rooms_df = self.find_empty_rooms()
        [empty_rooms_df.sort_values(by=['Building', 'Room Number', 'Day', 'Free From', 'Free To'], inplace=True)]
        empty_rooms_df.to_csv(output_file, index=False)


class LectureScheduleManager:
    def __init__(self, input_file: str, output_file: str):
        self.input_file = input_file
        self.output_file = output_file

    def process(self):
        # 1. 강의시간 파싱 후 DataFrame 반환
        parser = LectureParser(self.input_file)
        expanded_df = parser.expand_lecture_times()

        # 2. RoomScheduler에서 빈 강의실 시간대 분석
        scheduler = RoomScheduler(expanded_df)
        scheduler.save_empty_rooms_to_csv(self.output_file)


if __name__ == "__main__":
    # 실행 예시
    input_file_path = './sandol/crawler/source/report.xlsx'
    output_file_path = './sandol/crawler/source/empty_rooms_schedule.csv'

    manager = LectureScheduleManager(input_file_path, output_file_path)
    manager.process()

    print("처리 완료")
